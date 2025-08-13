from flask import send_file, request
from datetime import datetime
from pathlib import Path
from utils.config import load_config
from utils.error_hanlder import check_error
from utils.config import load_config
from database import DatabaseQueries, Database
from utils.config import db_path
from utils.error_hanlder import check_error
from email_invoice import email_invoice
import generate_invoice
import traceback
import os

def calculate_instant_tickets_sold(ReportID): # TODO: RETURNING ERROR MESSAGE
    msg_data = {"message": "", "message_type": ""}
    instant_tickets_sold_quantanties = check_error(DatabaseQueries.get_all_instant_tickets_sold_quantity(db_path, ReportID), msg_data, fallback=[])

    result = 0
    for ticket_sold in instant_tickets_sold_quantanties:
        try:
            result += (ticket_sold["Ticket_Sold_Quantity"] * ticket_sold["TicketPrice"])
        except (KeyError, TypeError) as e:
            if msg_data is not None:
                msg_data["message"] = f"Error calculating instant tickets sold: {str(e)}"
                msg_data["message_type"] = "error"
            return 0
    return result

def create_daily_invoice(ReportID, return_path_only=False):
    msg_data = {"message": "", "message_type": ""}
    config = load_config()
    invoiceLog = check_error(DatabaseQueries.get_table_for_invoice(db_path, ReportID), msg_data)
    if msg_data.get("message_type") == "error":
        return "ERROR: Unable to get the invoice table", "error"
    
    store_name = "Store Name" if load_config()["business_name"] is None else load_config()["business_name"] 
    address = "Store Address" if load_config()["business_address"] is None else load_config()["business_address"] 
    phone = "N/a" if load_config()["business_phone"] is None else load_config()["business_phone"] 
    email = "N/a" if load_config()["business_email"] is None else load_config()["business_email"] 
    
    store_info = {
        "Business Name": store_name,
        "Address": address,
        "Phone": phone,
        "Email": email
    }
    daily_report = check_error(DatabaseQueries.get_daily_report(db_path, ReportID), msg_data)
    
    if msg_data.get("message_type") == "error":
        return "ERROR: Unable to create daily invoice", "error"
    output_path = config.get('invoice_output_path')
    # Determine output directory
    if output_path and os.path.isdir(output_path):
        save_dir = output_path
    else:
        save_dir = str(Path.home() / "Downloads")
    now = datetime.now()
    invoice_number=f"{ReportID}"
    fileName=f"Invoice#{ReportID}-{now.strftime('%m-%d-%Y')}.pdf"
    full_path = os.path.join(save_dir, fileName)
    try:
        generate_invoice.generate_lottery_invoice_pdf(full_path, store_info, invoiceLog, invoice_number, daily_report)
        
        if return_path_only:
            return full_path, "success"
        
        return send_file(full_path, as_attachment=True), "success"
    except Exception as e:
        # Log or handle error appropriately
        print(f"Failed to generate/send invoice: {e}")
        return f"Error generating invoice: {e}", 500
    
def add_sales_log(book_id, lastest_ticket_number, game_number):
    msg_data = {"message": "", "message_type": ""}
    """
    Args:
        book_id (str)
        latest_ticket_number (str or int)
        game_number (str or int)
    """
    # Get the current state of the book
    activate_book_isAtTicketNumber = check_error(DatabaseQueries.get_activated_book_isAtTicketNumber(db_path, book_id), message_holder=msg_data)
    ticket_name = check_error(DatabaseQueries.get_ticket_name(db_path, game_number), message_holder=msg_data)
    
    # Build sales log entry
    sale_log_info = {
        "ActiveBookID": book_id,
        "prev_TicketNum": activate_book_isAtTicketNumber, # index 4 is the isAtTicketNumber
        "current_TicketNum": lastest_ticket_number,
        "Ticket_Name": ticket_name,
        "Ticket_GameNumber": game_number
    }
    
    check_error(Database.insert_sales_log(db_path, sale_log_info), message_holder=msg_data)

    return msg_data.get("message", ""), msg_data.get("message_type", "")

def do_submit_procedure():
    msg_data = {"message": "", "message_type": ""}
    try:
        next_ReportID = check_error(DatabaseQueries.next_report_ID(db_path), msg_data) # STRING 
        # Get form values
        daily_totals = {
            "ReportID": next_ReportID,
            "instant_sold": request.form.get('instant_sold'),
            "online_sold": request.form.get('online_sold'),
            "instant_cashed": request.form.get('instant_cashed'),
            "online_cashed":request.form.get('online_cashed'),
            "cash_on_hand": request.form.get('cash_on_hand')
        }
        
        # Insert the daily_totals in the Daily_Report Database.
        check_error(Database.insert_daily_totals(db_path, daily_totals), msg_data)
        # Update "Pending" SalesLog ReportID
        check_error(Database.update_pending_sales_log_report_id(db_path, next_ReportID), msg_data)
        # Update "Pending" TicketTimeLine ReportID
        check_error(Database.update_pending_TicketTimeLine_report_id(db_path, next_ReportID), msg_data)

        # Create a Invoice
        check_error(create_daily_invoice(next_ReportID), msg_data)
        
        # Remove sold out books from current ActivatedBooks table using there book ids
        sold_out_books = check_error(DatabaseQueries.get_all_sold_books(db_path, next_ReportID), msg_data)
        for book in sold_out_books:
            check_error(Database.deactivate_book(db_path, book["BookID"]), msg_data)
        # Update Database 
        # isAtTicketNumber in ActiviatedBooks needs to be set to current numbers from today's scans.
        # countingTicketNumber needs to be set to None since nothing is being counted after submit.
        check_error(Database.update_isAtTicketNumber(db_path), msg_data)
        check_error(Database.clear_countingTicketNumbers(db_path), msg_data)
        # TODO: File not found at given location error
        now = datetime.now()
        fileName=f"Invoice#{next_ReportID}-{now.strftime('%m-%d-%Y')}.pdf"
        email_invoice(filename=fileName)
        
        if msg_data.get("message_type") == "error":
            return msg_data["message"], msg_data["message_type"]
        return "SCANS SUBMITTED SUCCESSFULLY","success"
    except ValueError as ve:
        return str(ve), "error"
    except FileNotFoundError as fnf:
        return f"Invoice not found: {str(fnf)}", "error"
    except Exception as e:
        traceback.print_exc()
        return f"Unexpected error: {str(e)}", "error"