from flask import Blueprint, render_template, request, redirect, url_for
from database import Database, DatabaseQueries
from utils.config import db_path 
from utils.error_hanlder import check_error
from ScannedCodeInformationManagement import ScannedCodeManagement
from utils.tickets import insert_ticket
from utils.reports import calculate_instant_tickets_sold, add_sales_log, do_submit_procedure
from utils.config import load_config

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/scan_tickets', methods=["GET", "POST"])
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

@tickets_bp.route("/undo_scan", methods=["POST"])
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

    return redirect(url_for("tickets.scan_tickets", message=msg_data.get("message", ""), message_type=msg_data.get("message_type", ""))) 

@tickets_bp.route("/book_sold_out", methods=["POST", "GET"])
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
    return redirect(url_for("tickets.scan_tickets",  message=msg_data.get("message", ""), message_type=msg_data.get("message_type", "")))

@tickets_bp.route("/submit", methods=["GET", "POST"])
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
            return redirect(url_for("tickets.scan_tickets", **msg_data))
        else:
            return redirect(url_for("tickets.scan_tickets"))    
        
    except ValueError as e:
        return redirect(url_for("tickets.scan_tickets", message=str(e), message_type="error"))
