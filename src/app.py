import eventlet
eventlet.monkey_patch()
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import send_file
import os
from ScannedCodeInformationManagement import ScannedCodeManagement
import Database
import DatabaseQueries
import generate_invoice
import game_number_lookup_table
from utc_to_local_time import convert_utc_to_local
from datetime import datetime
import re
import traceback
from config_utils import load_config
from config_utils import update_ticket_order
from config_utils import update_invoice_output_path
from config_utils import update_business_info 
from datetime import datetime
from pathlib import Path
from email_invoice import email_invoice
from decorators import with_error_handling

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")  # Allow all for dev

# SQLite version is ≥ 3.31.0

# Get database path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_dir, 'Lottery_Management_Database.db')    

DEFAULT_DOWNLOADS_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

def check_error(result_or_callable, message_holder=None, fallback=None):
    """
    Evaluates a callable or result and handles standard (msg, 'error') patterns.

    Args:
        result_or_callable: A callable or pre-evaluated result.
        message_holder (dict, optional): A dictionary that holds "message" and "message_type".
        fallback (Any, optional): A fallback value to return if an error is detected.

    Returns:
        The original result if successful, or fallback if error is detected.
    """
    try:
        result = result_or_callable() if callable(result_or_callable) else result_or_callable

        if isinstance(result, tuple) and len(result) == 2:
            msg, msg_type = result
            if msg_type == "error":
                if message_holder is not None:
                    message_holder["message"] = msg
                    message_holder["message_type"] = msg_type
                return fallback
        return result
    except Exception as e:
        if message_holder is not None:
            message_holder["message"] = f"Unexpected Error: {e}"
            message_holder["message_type"] = "error"
        return fallback



@app.route('/scan_tickets', methods=["GET", "POST"])
def scan_tickets():
    msg_data = {"message": "", "message_type": ""}
    msg_data["message"] = request.args.get("message", "")
    msg_data["message_type"] = request.args.get("message_type", "")
    
    if request.method == "POST":
        # Get book ids for all the active books 
        all_active_book_ids = check_error(DatabaseQueries.get_all_active_book_ids(db=db_path), message_holder=msg_data)
        
        # Get relevant information from the scanned code
        scanned_code = request.form['scanned_code']
        scanned_info = ScannedCodeManagement(scanned_code=scanned_code, db_path=db_path)
        extracted_vals = scanned_info.extract_all_scanned_code()
        
        if extracted_vals == "INVALID BARCODE":
            msg_data["message"] = "INVALID BARCODE"
            msg_data["message_type"] = "error"
        elif extracted_vals["book_id"] not in all_active_book_ids:
            msg_data["message"] = "Book IS NOT ACTIVATED! PLEASE ACTIVATE BEFORE SCANNING."
            msg_data["message_type"] = "error"
        else:
            # Insert ticket
            scanID = scanned_code
            TicketName = check_error(DatabaseQueries.get_ticket_name(db_path, extracted_vals["game_number"]), message_holder=msg_data)
            check_error(insert_ticket(scanID, extracted_vals["book_id"], extracted_vals["ticket_number"], TicketName, extracted_vals["ticket_price"]), message_holder=msg_data)
            check_error(Database.update_counting_ticket_number(db_path, extracted_vals["book_id"], extracted_vals["ticket_number"]), message_holder=msg_data)
            # Add sales log
            check_error(add_sales_log(extracted_vals["book_id"], extracted_vals["ticket_number"], extracted_vals["game_number"]), message_holder=msg_data)
            msg_data["message"] = "TICKET SCANNED"
            msg_data["message_type"] = "success"

    # Get all the active books basically. In reality, making a table to show to the user using activated bookids.
    # Instant ticket sold calculation
    # Get the counting order to calc sold
    # Get activated ticket count
    return render_template("scan_tickets.html",activated_books=check_error(DatabaseQueries.get_scan_ticket_page_table(db=db_path), message_holder=msg_data),
            instant_tickets_sold_total=check_error(calculate_instant_tickets_sold(ReportID="Pending"), message_holder=msg_data),
            counting_order=load_config()['ticket_order'],
            activated_book_count=check_error(DatabaseQueries.count_activated_books(db_path), message_holder=msg_data, fallback=0),
            message=msg_data.get("message", ""),
            message_type=msg_data.get("message_type", ""))

@app.route("/undo_scan", methods=["POST"])
def undo_scan():
    book_id = request.form.get("book_id")
    msg_data = {"message": "", "message_type": ""}
    if book_id:
        try:
            # Step 1: Delete ticket
            check_error(Database.delete_TicketTimeLine_by_book_id(db_path, book_id), message_holder=msg_data)
            
            # Step 2: Delete sales log for that book and TicketTimeLine Log will be deleted automatically
            check_error(Database.delete_sales_log_by_book_id(db_path, book_id), message_holder=msg_data)

            # Step 3: Clear the counting ticket number
            check_error(Database.clear_counting_ticket_number(db_path, book_id), message_holder=msg_data)
            
            #Step 4: Mark Book Unsold
            check_error(Database.update_is_sold_for_book(db_path, False, book_id), message_holder=msg_data)

            msg_data["message"] = "UNDO SCAN SUCCESSFUL"
            msg_data["message_type"] = "success"
        except ValueError as ve:
            msg_data["message"] = str(ve)
            msg_data["message_type"] = "error"
        except Exception as e:
            msg_data["message"] = f"Unexpected error: {str(e)}"
            msg_data["message_type"] = "error"

    return redirect(url_for("scan_tickets", message=msg_data.get("message", ""), message_type=msg_data.get("message_type", ""))) 

@app.route("/book_sold_out", methods=["POST", "GET"])
def book_sold_out():
    msg_data = {"message": "", "message_type": ""}
    try:
        book_id = request.form.get("book_id")
        if not book_id:
            raise ValueError("No Book ID provided.")
        # Step 1: Mark book as sold
        # Tell Database book is sold out - sets it to be removed from activated tickets
        check_error(Database.update_is_sold_for_book(db_path, True, book_id), message_holder=msg_data)
        
        # Step 2: Get book info
        # Update the closing number for book
        book = check_error(DatabaseQueries.get_book(db_path, book_id), message_holder=msg_data)
        game_number = book[1]
        book_amount = book[3]
        TicketPrice = book[4]
        
        config = load_config()
        if config["ticket_order"] == "ascending":
            sold_out_val = book_amount
        elif config["ticket_order"] == "descending":
            sold_out_val = -1
        else:
            raise ValueError("Invalid ticket_order in config")
        
        # Step 4: Update counting ticket number
        check_error(Database.update_counting_ticket_number(db_path, book_id, sold_out_val), message_holder=msg_data)
        
        # Step 5: Add ticket timeline entry
        TicketName = check_error(DatabaseQueries.get_ticket_name(db_path, game_number), message_holder=msg_data)
        scanID = f"{game_number}{book_id}998{TicketPrice}{book_amount}" # -----TicketNumber 998 in scannID means BookSoldOut.
        # A Integrety error from insert_ticket implies duplicate insertion which is ok here because of the undo button.
        check_error(insert_ticket(scanID, book_id, -1, TicketName, TicketPrice), message_holder=msg_data)
        
        # Step 6: Add sales log
        # TicketNumber is sold_out_val here
        check_error(add_sales_log(book_id, sold_out_val, game_number), message_holder=msg_data)
        
        msg_data["message"] = "BOOK MARKED AS SOLD OUT"
        msg_data["message_type"] = "success"
    except ValueError as ve:
        msg_data["message"] = str(ve)
        msg_data["message_type"] = "error"
    except Exception as e:
        msg_data["message"] = "Unexpected Error: ".upper() + f"{str(e)}"
        msg_data["message_type"] = "error"
    return redirect(url_for("scan_tickets",  message=msg_data.get("message", ""), message_type=msg_data.get("message_type", "")))

def insert_ticket(scanID, BookID, TicketNumber, TicketName, TicketPrice, ReportID=None):
    msg_data = {"message": "", "message_type": ""}
    ticket_info = {
        "ScanID": scanID,
        "BookID": BookID,
        "TicketNumber": TicketNumber,
        "TicketName": TicketName,
        "TicketPrice": TicketPrice
    }
    if ReportID:
        ticket_info["ReportID"] = ReportID
    # Insert this ticket in TicketTimeline
    check_error(Database.insert_ticket_to_TicketTimeline_table(db_path, ticket_info), message_holder=msg_data)

    return msg_data.get("message", ""), msg_data.get("message_type", "")
    

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

@app.route("/update_salesLog", methods=["GET", "POST"])
def update_sales_log():
    msg_data = {"message": "", "message_type": ""}
    updated_report_ids = []
    try:
        data = request.get_json()
        book_id = data.get('bookID')
        report_id = data.get("reportID") # str type
        open = data.get("open")
        close = data.get("close")
        
        report_id_int = int(report_id)
        previous_reportID = report_id_int - 1
        next_reportID = report_id_int + 1
        latest_reportID = int(check_error(lambda: DatabaseQueries.next_report_ID(db_path), msg_data))
        
        game_number = check_error(DatabaseQueries.get_game_num_of(db_path, book_id), msg_data)
        is_book_sold = check_error(DatabaseQueries.is_sold(db_path, book_id), msg_data)
        
        book = check_error(DatabaseQueries.get_book(db_path, book_id), msg_data)
        TicketName = check_error(DatabaseQueries.get_ticket_name(db_path, game_number), msg_data)
        scanID = f"{game_number}{book_id}{close}{TicketPrice}{book_amount}" 
        book_amount = book[3]
        TicketPrice = book[4]
        
        # Main update for current report
        check_error(Database.update_sales_log_prev_TicketNum(db_path, open, report_id, book_id), msg_data)
        check_error(Database.update_sales_log_current_TicketNum(db_path, close, report_id, book_id), msg_data)
        updated_report_ids.append(report_id_int)

        # Book is sold and user now closes it (removing sold status)
        if is_book_sold and close != "-1":
            # Update Is_Sold attribute to not sold for this book id.
            check_error(Database.update_is_sold_for_book(db_path, False, book_id), msg_data)
            # Update salesLog and TicketTimeline
            for id in range(report_id_int + 1, latest_reportID + 1):
                TicketName = check_error(DatabaseQueries.get_ticket_name(db_path, game_number), msg_data)
                # Add salesLog
                sale_log_info = {
                "ReportID": str(id), 
                "ActiveBookID": book_id,
                "prev_TicketNum": close, # index 4 is the isAtTicketNumber
                "current_TicketNum": close,
                "Ticket_Name": TicketName,
                "Ticket_GameNumber": game_number
                }
                check_error(Database.insert_sales_log(db_path, sale_log_info), msg_data)
                # A update in sale log means the instant sold should also be updated
                instant_sold = check_error(calculate_instant_tickets_sold(id), msg_data)
                check_error(Database.update_sale_report_instant_sold(db_path, instant_sold, id), msg_data)
                # Insert ticket for the book sold out
                check_error(insert_ticket(scanID, book_id, close, TicketName, TicketPrice, str(id)), msg_data)
            
            # Re-activate book with correct ticket position
            activate_book_info = {
                "ActivationID": scanID,
                "ActiveBookID": book_id,
                "isAtTicketNumber": close
            }
            check_error(Database.insert_book_to_ActivatedBook_table(database_path=db_path, active_book_info=activate_book_info), msg_data)

        # Update previous report if it exists
        if (not previous_reportID < 1):
            check_error(Database.update_ticketTimeline_ticketnumber(db_path, previous_reportID, book_id, open), msg_data)
            check_error(Database.update_sales_log_current_TicketNum(db_path, open, previous_reportID, book_id), msg_data)
            prev_instant_sold = check_error(calculate_instant_tickets_sold(previous_reportID), msg_data)
            check_error(Database.update_sale_report_instant_sold(db_path, prev_instant_sold, previous_reportID), msg_data)
            updated_report_ids.append(previous_reportID)
            
        # Update next report if it exists
        if (next_reportID <= latest_reportID):
            check_error(Database.update_sales_log_prev_TicketNum(db_path, close, next_reportID, book_id), msg_data)
            next_instant_sold = check_error(calculate_instant_tickets_sold(next_reportID), msg_data)
            check_error(Database.update_sale_report_instant_sold(db_path, next_instant_sold, next_reportID), msg_data)
            updated_report_ids.append(next_reportID)

        # If current is the latest report, update isAtTicketNumber
        if (latest_reportID == report_id_int):
            check_error(Database.update_isAtTicketNumber_val(db_path, book_id, close), msg_data)
        # Update ticket timeline and instant sold for current
        # A update in sale log means the instant sold should also be updated
        instant_sold = check_error(calculate_instant_tickets_sold(report_id), msg_data)
        check_error(Database.update_sale_report_instant_sold(db_path, instant_sold, report_id), msg_data)
        check_error(Database.update_ticketTimeline_ticketnumber(db_path, report_id, book_id, close), msg_data)
        
        return jsonify({"redirect_url": url_for("edit_single_report", report_id=report_id, updated_report_ids=updated_report_ids.__str__(),  message=msg_data.get("message", ""), message_type=msg_data.get("message_type", ""))})
    except Exception as e: 
        msg_data["message"] = str(e)
        msg_data["message_type"] = "error"
        safe_report_id = report_id if 'report_id' in locals() else "unknown"
        return jsonify({"redirect_url": url_for("edit_single_report", report_id=safe_report_id, updated_report_ids=updated_report_ids.__str__(), message=str(e), message_type="error")})
    

@app.route("/update_sale_report/<report_id>", methods=["GET","POST"])
def update_sale_report(report_id):
    msg_data = {"message": "", "message_type": ""}
    try:
        if request.method == "POST":
            instant_sold = request.form["instant_sold"]
            online_sold = request.form["online_sold"]
            instant_cashed = request.form["instant_cashed"]
            online_cashed = request.form["online_cashed"]
            cash_on_hand = request.form["cash_on_hand"]
            
            check_error(Database.update_sale_report(db_path, instant_sold, online_sold, instant_cashed, online_cashed, cash_on_hand, report_id), message_holder=msg_data)
        return redirect(url_for("edit_single_report", report_id=report_id, updated_report_ids="None"), message=msg_data.get("message", ""), message_type=msg_data.get("message_type", ""))
    except ValueError as e:
        return redirect(url_for("edit_single_report", report_id=report_id, updated_report_ids="None", message=str(e), message_type="error"))
 
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

@app.route("/submit", methods=["GET", "POST"])
def submit():
    msg_data = {"message": "", "message_type": ""}

    try:
        if check_error(DatabaseQueries.can_Submit(db_path), msg_data, fallback=False):
            result = do_submit_procedure()
            # In case result is an error message
            if isinstance(result, tuple) and result[1] == "error":
                msg_data["message"] = result[0]
                msg_data["message_type"] = result[1]
        # Redirect with message if any
        if msg_data["message"]:
            return redirect(url_for("scan_tickets", **msg_data))
        else:
            return redirect(url_for("scan_tickets"))    
        
    except ValueError as e:
        return redirect(url_for("scan_tickets", message=str(e), message_type="error"))

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
    
    

def create_daily_invoice(ReportID, return_path_only=False):
    msg_data = {"message": "", "message_type": ""}
    config = load_config()
    invoiceLog = check_error(DatabaseQueries.get_table_for_invoice(db_path, ReportID), msg_data)
    
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
            return full_path
        
        return send_file(full_path, as_attachment=True)
    except Exception as e:
        # Log or handle error appropriately
        print(f"Failed to generate/send invoice: {e}")
        return f"Error generating invoice: {e}", 500

@app.route('/')
def home():
    # While loading the home page initalize the database. 
    Database.initialize_database(db_path)
    return render_template('index.html')

@app.route('/books_managment', methods=["GET", "POST"])
def books_managment():
    msg_data = {"message": request.args.get('message', ''), "message_type": request.args.get('message_type', '')}
    # The redirect from /activate will generate a URL like: 
    # /books_managment?activate_book_message=SomeMessage&activate_book_message_type=success
    # request.args.get('activate_book_message', '') will then get these arguments
    
    # Books info for the books table to display on screen 
    books = check_error(DatabaseQueries.get_books(db=db_path), msg_data, fallback=[])
    # Setting TicketNames
    if books:
        for book in books:
            game_number = book["GameNumber"]
            book["TicketName"] = check_error(DatabaseQueries.get_ticket_name(db_path, game_number), fallback="N/A")
        
    # Get activated books (just the BookIDs)
    activated_books = check_error(DatabaseQueries.get_activated_books(db_path), msg_data, fallback=[])  # should return a list of dicts or a list of IDs
    activated_ids = {book['ActiveBookID'] for book in activated_books}  # Use set for faster lookup
    
    if request.method == 'POST':
        scanned_code = request.form['add_book_code']
        add_result = check_error(lambda: add_book_procedure(scanned_code), msg_data)
        if isinstance(add_result, tuple) and add_result[1] == "error":
            msg_data["message"], msg_data["message_type"] = add_result
    
    return {
        "books": books,
        "activated_ids": activated_ids,
        "message": msg_data.get("message", ""),
        "message_type": msg_data.get("message_type", "")
    }

def add_book_procedure(scanned_code):
    scanned_info = ScannedCodeManagement(scanned_code=scanned_code, db_path=db_path)
    extracted_vals = scanned_info.extract_all_scanned_code()
    
    if extracted_vals == "INVALID BARCODE":
        return "INVALID BARCODE", "error" # message, message_type
    else:
        # TODO: SHOULD RETURN ERRORS
        lookup_message, lookup_message_type = game_number_lookup_table.insert_new_ticket_name_to_lookup_table(db_path)
        if lookup_message_type == "error":
            # Log or attach a warning, but continue
            warning_message = f"Book added, but TicketName update failed: {lookup_message}"
        else:
            warning_message = None
        book_info = {
            "BookID": extracted_vals["book_id"],
            "GameNumber": extracted_vals["game_number"],
            "Is_Sold": False,
            "BookAmount": extracted_vals["book_amount"],
            "TicketPrice": extracted_vals["ticket_price"]
        }
        book_insert_msg, book_insert_type = Database.insert_book_info_to_Books_table(database_path=db_path, book_info=book_info)
        # Combine messages if needed
        if warning_message and book_insert_type == "success":
            return warning_message, "error"

        return book_insert_msg, book_insert_type
    
@app.route('/delete_book', methods=['POST', 'GET'])
def delete_book():
    msg_data = {"message": "", "message_type": ""}
    try:
        data = request.get_json()
        if not data or 'bookID' not in data:
            raise ValueError("Missing 'bookID' in request data.")
        book_id = data.get('bookID')
        print(f"Deleting: {book_id}")
        # Deactivate first, then delete
        # Safely run deactivation and deletion with error checking
        check_error(lambda: Database.deactivate_book(db_path, book_id), msg_data)
        check_error(lambda: Database.delete_Book(db_path, book_id), msg_data)

        if msg_data["message_type"] == "error":
            return jsonify({
                "redirect_url": url_for('books_managment'),
                "message": msg_data["message"],
                "message_type": msg_data["message_type"]
            }), 500

        
        return jsonify({ "redirect_url": url_for('books_managment'),
                        "message": f"Book {book_id} deleted successfully.",
                        "message_type": "success"})
    except Exception as e:
        print(f"Error deleting book {book_id}: {e}")
        return jsonify({
            "redirect_url": url_for('books_managment'),
            "message": f"Error deleting book: {str(e)}",
            "message_type": "error"
        }), 500

@app.route('/business_profile', methods=["GET","POST"])
def business_profile():
    message = None
    message_type = "error"
    if request.method == "POST":
        config = load_config()
        
        # Process form input with fallback to config
        form_data = extract_businessProfileForm_data(config)
        
        # Validate and update business info fields
        errors = validate_and_update_business_info(form_data)
        if errors:
            message = errors[0]  # Only show the first error
        else:
            message = "Business profile updated successfully."
            message_type = "success"
    
    # Load current config for rendering
    config = load_config()
    return render_template(
        "business_profile.html",
        business_Info={
            "Name": config["business_name"],
            "Address": config["business_address"],
            "Phone": config["business_phone"],
            "Email": config["business_email"],
        },
        message=message,
        message_type=message_type
    )

@app.route('/settings', methods=["GET","POST"])
def settings():
    message = None
    message_type = "warning"
    if request.method == "POST":
        config = load_config()
    
        # Process form input with fallback to config
        form_data = extract_settingForm_data(config)

        # Update ticket order
        update_ticket_order(form_data["ticket_order"])

        # Validate and update invoice output path
        valid_output, warning_message = validate_invoice_output_path(form_data["output_path"])
        if warning_message:
            message = warning_message
        update_invoice_output_path(valid_output)

    # Load current config for rendering
    config = load_config()
    return render_template(
        "settings.html",
        counting_order=config["ticket_order"],
        invoice_output_path=config["invoice_output_path"],
        message=message,
        message_type=message_type
    )

def extract_settingForm_data(config):
    return {
        "ticket_order": request.form.get("ticket_order") or config["ticket_order"],
        "output_path": request.form.get("outputPath") or config["invoice_output_path"]
    }

def extract_businessProfileForm_data(config):
    return {
        "business_name": request.form.get("BusinessName") or config["business_name"],
        "business_address": request.form.get("BusinessAddress") or config["business_address"],
        "business_phone": request.form.get("BusinessPhone") or config["business_phone"],
        "business_email": request.form.get("BusinessEmail") or config["business_email"]
    }

def validate_invoice_output_path(path):
    if os.path.isdir(path):
        return path, None
    return DEFAULT_DOWNLOADS_PATH, "Resetting to DEFAULT PATH (invalid output path)"

def validate_and_update_business_info(data):
    errors = []

    # Business Name (always updated without validation)
    update_business_info(name="business_name", value=data["business_name"])

    # Address validation
    address = data["business_address"]
    if address == "" or re.match("^(\\d{1,}) [a-zA-Z0-9\\s]+(\\,)? [a-zA-Z]+(\\,)? [A-Z]{2} [0-9]{5,6}$", address):
        update_business_info(name="business_address", value=address)
    else:
        update_business_info(name="business_address", value="")
        errors.append("Not a valid ADDRESS!")

    # Phone number validation
    phone = data["business_phone"]
    if phone == "" or re.fullmatch(r"^\+?\d{10,15}$", phone):
        update_business_info(name="business_phone", value=phone)
    else:
        update_business_info(name="business_phone", value="")
        errors.append("Not a valid PHONE NUMBER!")

    # Email validation (allow empty field)
    email = data["business_email"]
    if email == "" or re.fullmatch(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        update_business_info(name="business_email", value=email)
    else:
        update_business_info(name="business_email", value="")
        errors.append("Not a valid EMAIL!")

    return errors
    
@app.route('/deactivate_book', methods=['POST', 'GET'])
def deactivate_book():
    msg_data = {"message": "", "message_type": ""}
    try:
        data = request.get_json()
        book_id = data.get('bookID')
        print(f"Deactivating: {book_id}")
        
        check_error(Database.deactivate_book(db_path, book_id), msg_data)
        if msg_data["message_type"] == "error":
            return jsonify({
                "redirect_url": url_for('books_managment'),
                "message": msg_data["message"],
                "message_type": msg_data["message_type"]
            }), 500
        return jsonify({ "redirect_url": url_for('books_managment') })
    except Exception as e:
        print(f"Unexpected error while deactivating book {book_id}: {e}")
        return jsonify({
            "redirect_url": url_for('books_managment'),
            "message": f"Unexpected error deactivating book: {e}",
            "message_type": "error"
        }), 500
    

@app.route('/activate_book', methods=["GET", "POST"])
def activate_book():
    message = ""
    message_type = ""
    
    if request.method == 'POST':
        scanned_code = request.form.get('activate_book_code')
        message, message_type = activate_book_procedure(scanned_code) 
        
    return redirect(url_for("books_managment", message=message, message_type=message_type))

def activate_book_procedure(scanned_code):
    msg_data = {"message": "", "message_type": ""}
    try:
        scanned_info = ScannedCodeManagement(scanned_code=scanned_code, db_path=db_path)
        extracted_vals = scanned_info.extract_all_scanned_code()
        
        if extracted_vals == "INVALID BARCODE":
            return "INVALID BARCODE", "error" # message, message_type
        # The book being activated must already be registered in the system. 
        # So check to make sure that the book being instered is prensent in the system and is not already activated. 
        book_exists = DatabaseQueries.is_book(db=db_path, book_id=extracted_vals["book_id"])
        book_is_activated = DatabaseQueries.is_activated_book(db=db_path, activated_book_id=extracted_vals["book_id"])

        if not book_exists:
            return "BOOK DOES NOT EXISTS IN BOOKS DATABASE!", "error"

        if book_is_activated:
            return "BOOK HAS ALREADY BEEN ACTIVATED!", "error"
        

        activate_book_info = {
            "ActivationID": scanned_code,
            "ActiveBookID": extracted_vals["book_id"],
            "isAtTicketNumber": extracted_vals["ticket_number"]
        }
        was_active_ticket_num = check_error(DatabaseQueries.was_activated(db_path, activate_book_info["ActiveBookID"]), msg_data, fallback=None)
        # check to see if the book has been activated previosly or not
        if was_active_ticket_num is not None and was_active_ticket_num > -1:
            activate_book_info["isAtTicketNumber"] = was_active_ticket_num
        
        # Final activation step
        result = check_error(
            Database.insert_book_to_ActivatedBook_table(
                database_path=db_path,
                active_book_info=activate_book_info
            ),
            message_holder=msg_data
        )

        # Return error or success response
        if msg_data["message_type"] == "error":
            return msg_data["message"], msg_data["message_type"]
        return result        
    except Exception as e:
        return f"Unexpected Error: {str(e)}", "error"


@app.route('/edit_reports')
def edit_reports():
    # Safely load all reports
    msg_data = {"message": "", "message_type": ""}
    sales_reports = check_error(DatabaseQueries.get_all_sales_reports(db_path), msg_data, fallback=[])
    
    # Convert to local date and time and filter
    local_reports = []
    filter_date = request.args.get("date")
    
    filter_time = None
    filter_time_military = request.args.get("time")
    if filter_time_military:
        try:
            filter_time_obj = datetime.strptime(filter_time_military, "%H:%M")
            # Format to regular time with AM/PM
            filter_time = filter_time_obj.strftime("%I:%M %p")
        except ValueError:
            msg_data["message"] = "Invalid time format. Please use HH:MM (24-hour format)."
            msg_data["message_type"] = "error"
            filter_time = None  # Fail gracefully
    
    # convert sales report date and time from utc to local
    for report in sales_reports:
        try:
            utc_date = datetime.strptime(report["ReportDate"], "%Y-%m-%d").date()
            utc_time = datetime.strptime(report["ReportTime"], "%H:%M:%S").time()
            local_date = convert_utc_to_local(utc_date, 'America/New_York').strftime("%Y-%m-%d")
            local_time = convert_utc_to_local(utc_time, 'America/New_York').strftime("%I:%M %p")
            # Filter logic
            match = True
            if filter_date:
                if local_date != filter_date:
                    match = False
            if filter_time:
                if not local_time.startswith(filter_time):
                    match = False

            if match:
                report["ReportDate"] = local_date
                report["ReportTime"] = local_time
                local_reports.append(report)
        except Exception as e:
            msg_data["message"] = f"Skipping report due to error: {e}"
            msg_data["message_type"] = "error"
            continue
    return render_template("edit_reports.html", sales_reports=local_reports, message=msg_data.get("message", ""), message_type=msg_data.get("message_type", ""))

@app.route("/edit_report/<report_id>/<updated_report_ids>",  methods=["GET", "POST"])
def edit_single_report(report_id, updated_report_ids=None):
    message = request.args.get("message", "")
    message_type = request.args.get("message_type", "")
    
    msg_data = {"message": message, "message_type": message_type}
    # Query the sales logs related to this report ID
    sales_logs = check_error(DatabaseQueries.get_sales_log(db_path, report_id), message_holder=msg_data, fallback=[])
    sale_report = check_error(DatabaseQueries.get_daily_report(db_path, report_id), message_holder=msg_data, fallback={})
    # Instant ticket sold recalculation
    if sale_report:
        instant_tickets_sold_total = check_error(calculate_instant_tickets_sold(ReportID=report_id), msg_data, fallback=0)
        sale_report["InstantTicketSold"] = instant_tickets_sold_total
    # Get the counting order to calc sold
    counting_order = load_config()['ticket_order']
    return render_template("edit_single_report.html", 
                           report_id=report_id, 
                           sales_logs=sales_logs, 
                           sale_report=sale_report, 
                           counting_order=counting_order, 
                           updated_report_ids=updated_report_ids,
                           message=message,
                           message_type=message_type) 

@app.route('/download/<int:report_id>', methods=['GET']) # change to GET for easier triggering
def download_modified_report(report_id): 
    msg_data = {"message": "", "message_type": ""}
    result = check_error(lambda: create_daily_invoice(report_id), msg_data)
    
    if msg_data.get("message_type") == "error":
        return msg_data["message"], msg_data["message_type"]
    
    return result


@socketio.on('connect')
def on_connect():
    print("Client connected")

@app.route('/receive', methods=['POST'])
def receive():
    barcode = request.form.get('barcode')
    print(f"Received barcode: {barcode}")
    with app.app_context():
        socketio.emit("barcode_scanned", {"barcode": barcode})
    return "Received"


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
    
