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
from config_utils import load_config
from config_utils import update_ticket_order
from config_utils import update_invoice_output_path


app = Flask(__name__)
# Feature: Edit lottery, recreate invoice report?
# Feature: Error UI for user
# Issue: Sold should take into account that a ticket was found today
# Issue: undo isSold?
# SQLite version is ≥ 3.31.0

# Get database path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_dir, 'Lottery_Management_Database.db')

@app.route('/scan_tickets', methods=["GET", "POST"])
def scan_tickets():

    if request.method == "POST":
        # Get book ids for all the active books 
        all_active_book_ids = DatabaseQueries.get_all_active_book_ids(db=db_path)
        
        # Get relevant information from the scanned code
        scanned_code = request.form['scanned_code']
        scanned_info = ScannedCodeManagement(scanned_code=scanned_code)
        scanned_book_id = scanned_info.get_book_id()
        
        # If the book id from scanned code is present in the active books then it is valid.
        if scanned_book_id in all_active_book_ids:
            # Insert ticket
            scanID = scanned_code
            book_id = scanned_info.get_book_id()
            TicketNumber = scanned_info.get_ticket_num()
            TicketPrice = scanned_info.get_ticket_price()
            game_number = scanned_info.get_game_num()
            TicketName = DatabaseQueries.get_ticket_name(db_path, game_number)
            insert_ticket(scanID, book_id, TicketNumber, TicketName, TicketPrice)
            # Add the closing number 
            Database.update_counting_ticket_number(db_path, book_id, TicketNumber)
            # Add sales log
            add_sales_log(book_id, TicketNumber, game_number)
        else:
            print("UnActivated Book")
    # Get all the active books basically. In reality, making a table to show to the user using activated bookids.
    activate_books = DatabaseQueries.get_scan_ticket_page_table(db_path=db_path)
    
    # Instant ticket sold calculation
    instant_tickets_sold_total = calculate_instant_tickets_sold(ReportID="Pending") 
    
    # Get the counting order to calc sold
    counting_order = load_config()['ticket_order']
    return render_template('scan_tickets.html', activated_books=activate_books, instant_tickets_sold_total=instant_tickets_sold_total, counting_order=counting_order)

@app.route("/undo_scan", methods=["POST"])
def undo_scan():
    book_id = request.form.get("book_id")
    if book_id:
        try:
            # Step 1: Delete ticket
            Database.delete_TicketTimeLine_by_book_id(db_path, book_id)
            
            # Step 2: Delete sales log for that book and TicketTimeLine Log will be deleted automatically
            Database.delete_sales_log_by_book_id(db_path, book_id)

            # Step 3: Clear the counting ticket number
            Database.clear_counting_ticket_number(db_path, book_id)

            print("Undo successful.")
        except Exception as e:
            print(f"Undo failed: {e}")

    return redirect(url_for("scan_tickets")) 

@app.route("/book_sold_out", methods=["POST", "GET"])
def book_sold_out():
    book_id = request.form.get("book_id")
    # Tell Database book is sold out - sets it to be removed from activated tickets
    Database.update_is_sold_for_book(db_path, book_id)
    # Update the closing number for book
    Database.update_counting_ticket_number(db_path, book_id, -1)
    # Insert to TicketTimeline
    book = DatabaseQueries.get_book(db_path, book_id)
    game_number = book[1]
    book_amount = book[2]
    TicketPrice = book[3]
    TicketNumber = -1
    TicketName = DatabaseQueries.get_ticket_name(db_path, game_number)
    scanID = f"{game_number}{book_id}998{TicketPrice}{book_amount}" # -----TicketNumber 998 in scannID means -1.
    insert_ticket(scanID, book_id, TicketNumber, TicketName, TicketPrice)
    # Add a sales log
    add_sales_log(book_id, TicketNumber, game_number)
    
    return redirect(url_for("scan_tickets"))  # or your page name

def insert_ticket(scanID, BookID, TicketNumber, TicketName, TicketPrice):
    ticket_info = {
        "ScanID": scanID,
        "BookID": BookID,
        "TicketNumber": TicketNumber,
        "TicketName": TicketName,
        "TicketPrice": TicketPrice
    }
    # Insert this ticket in TicketTimeline
    Database.insert_ticket_to_TicketTimeline_table(db_path, ticket_info)
    

def add_sales_log(book_id, lastest_ticket_number, game_number):
    """
    Args:
        book_id (STRING)
        lastest_ticket_number (STRING)
        game_number (STRING)
    """
    # Add a sales log for this scan
    activate_book_isAtTicketNumber = DatabaseQueries.get_activated_book_isAtTicketNumber(db_path, book_id)
    # ---- Calulateing sold (999 will change this)
    sale_log_info = {
        "ActiveBookID": book_id,
        "prev_TicketNum": activate_book_isAtTicketNumber[0], # index 4 is the isAtTicketNumber
        "current_TicketNum": lastest_ticket_number,
        "Ticket_Name": DatabaseQueries.get_ticket_name(db_path, game_number),
        "Ticket_GameNumber": game_number
    }
    Database.insert_sales_log(db_path, sale_log_info)
    
@app.route("/update_salesLog", methods=["GET", "POST"])
def update_sales_log():
    data = request.get_json()
    book_id = data.get('bookID')
    report_id = data.get("reportID")
    open = data.get("open")
    close = data.get("close")
    
    Database.update_sales_log_prev_TicketNum(db_path, open, report_id, book_id)
    Database.update_sales_log_current_TicketNum(db_path, close, report_id, book_id)

    previous_reportID = int(report_id) - 1
    next_reportID =  int(report_id) + 1
    latest_reportID = int(DatabaseQueries.next_report_ID(db_path)) - 1

    if (not previous_reportID < 1):
        Database.update_ticketTimeline_ticketnumber(db_path, previous_reportID, book_id, open)
        Database.update_sales_log_current_TicketNum(db_path, open, previous_reportID, book_id)
        prev_instant_sold = calculate_instant_tickets_sold(previous_reportID)
        Database.update_sale_report_instant_sold(db_path, prev_instant_sold, previous_reportID)
    
    if (next_reportID <= latest_reportID):
        Database.update_sales_log_prev_TicketNum(db_path, close, next_reportID, book_id)
        next_instant_sold = calculate_instant_tickets_sold(next_reportID)
        Database.update_sale_report_instant_sold(db_path, next_instant_sold, next_reportID)

    if (latest_reportID == report_id):
        Database.update_isAtTicketNumber_val(db_path, book_id, close)



    # A update in sale log means the instant sold should also be updated
    instant_sold = calculate_instant_tickets_sold(report_id)
    Database.update_sale_report_instant_sold(db_path, instant_sold, report_id)
    Database.update_ticketTimeline_ticketnumber(db_path, report_id, book_id, close)
    
    return jsonify({ "redirect_url": url_for("edit_single_report", report_id=report_id)})

@app.route("/update_sale_report/<report_id>", methods=["GET","POST"])
def update_sale_report(report_id):
    if request.method == "POST":
        instant_sold = request.form["instant_sold"]
        online_sold = request.form["online_sold"]
        instant_cashed = request.form["instant_cashed"]
        online_cashed = request.form["online_cashed"]
        cash_on_hand = request.form["cash_on_hand"]
        
        Database.update_sale_report(db_path, instant_sold, online_sold, instant_cashed, online_cashed, cash_on_hand, report_id)
    return redirect(url_for("edit_single_report", report_id=report_id))
 
def calculate_instant_tickets_sold(ReportID):
    instant_tickets_sold_quantanties = DatabaseQueries.get_all_instant_tickets_sold_quantity(db_path, ReportID)
    result = 0
    for ticket_sold in instant_tickets_sold_quantanties:
        result += (ticket_sold["Ticket_Sold_Quantity"] * ticket_sold["TicketPrice"])
    
    return result

@app.route("/submit", methods=["GET", "POST"])
def submit():
    if DatabaseQueries.can_Submit(db_path):
        do_submit_procedure()
    
    return redirect(url_for("scan_tickets"))

def do_submit_procedure():
    next_ReportID = DatabaseQueries.next_report_ID(db_path) # STRING 
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
    Database.insert_daily_totals(db_path, daily_totals)
    # Update "Pending" SalesLog ReportID
    Database.update_pending_sales_log_report_id(db_path, next_ReportID)
    # Update "Pending" TicketTimeLine ReportID
    Database.update_pending_TicketTimeLine_report_id(db_path, next_ReportID)
    # Create a Invoice
    create_daily_invoice(next_ReportID)
    # Remove sold out books from current ActivatedBooks table using there book ids
    sold_out_books = DatabaseQueries.get_all_sold_books(db_path, next_ReportID)
    for book in sold_out_books:
        Database.deactivate_book(db_path, book["BookID"])
    # Update Database 
    # isAtTicketNumber in ActiviatedBooks needs to be set to current numbers from today's scans.
    # countingTicketNumber needs to be set to None since nothing is being counted after submit.
    Database.update_isAtTicketNumber(db_path)
    Database.clear_countingTicketNumbers(db_path)

def create_daily_invoice(ReportID, store_name="Scuttlebutts Liquors", address="407 Main St, Fairhaven, MA 02719", phone="(508) 999-5253", email="N/a", fileName="invoice_lottery.pdf"):

    
    invoiceLog = DatabaseQueries.get_table_for_invoice(db_path, ReportID)
    store_info = {
        "Business Name": store_name,
        "Address": address,
        "Phone": phone,
        "Email": email
    }
    daily_report = DatabaseQueries.get_daily_report(db_path, ReportID)
    invoice_number="Invoice001"
    generate_invoice.generate_lottery_invoice_pdf(fileName, store_info, invoiceLog, invoice_number, daily_report)
    

@app.route('/')
def home():
    # While loading the home page initalize the database. 
    Database.initialize_database(db_path)
    game_number_lookup_table.insert_new_ticket_name_to_lookup_table(db_path)
    return render_template('index.html')

@app.route('/books_managment', methods=["GET", "POST"])
def books_managment():
    status_message_add_book = ""
    
    if request.method == 'POST':
        scanned_code = request.form['add_book_code']
        add_book_procedure(scanned_code)
        status_message_add_book = "Book added to the database."
    
    # Books info for the books table to display on screen 
    books = DatabaseQueries.get_books(db=db_path)
    
    for book in books:
        game_number = book["GameNumber"]
        book["TicketName"] = DatabaseQueries.get_ticket_name(db_path, game_number)

    # Get activated books (just the BookIDs)
    activated_books = DatabaseQueries.get_activated_books(db_path)  # should return a list of dicts or a list of IDs
    activated_ids = {book['ActiveBookID'] for book in activated_books}  # Use set for faster lookup
    
    status_message_activate_book = request.args.get('status_message_activate_book')
    
    return render_template('books_managment.html', books=books, activated_ids=activated_ids, status_message_add_book=status_message_add_book, status_message_activate_book=status_message_activate_book)

def add_book_procedure(scanned_code):
    scanned_info = ScannedCodeManagement(scanned_code=scanned_code)
    game_number = scanned_info.get_game_num()
    book_info = {
        "BookID": scanned_info.get_book_id(),
        "GameNumber": game_number,
        "Is_Sold": False,
        "BookAmount": scanned_info.get_book_amount(),
        "TicketPrice": scanned_info.get_ticket_price()
    }
    Database.insert_book_info_to_Books_table(database_path=db_path, book_info=book_info)
    
@app.route('/delete_book', methods=['POST', 'GET'])
def delete_book():
    data = request.get_json()
    book_id = data.get('bookID')
    print(f"Deleting: {book_id}")
    Database.deactivate_book(db_path, book_id)
    Database.delete_Book(db_path, book_id)

    return jsonify({ "redirect_url": url_for('books_managment') })

@app.route('/settings', methods=["GET","POST"])
def settings():
    ticket_order = request.form.get("ticket_order")
    invoice_output_request = request.form.get("outputPath")
    
    update_ticket_order(ticket_order)
    update_invoice_output_path(invoice_output_request)

    counting_order = load_config()['ticket_order']
    invoice_output_path = load_config()['invoice_output_path']
    return render_template("settings.html", counting_order = counting_order, invoice_output_path = invoice_output_path)
    
@app.route('/deactivate_book', methods=['POST', 'GET'])
def deactivate_book():
    data = request.get_json()
    book_id = data.get('bookID')
    print(f"Deactivating: {book_id}")
    Database.deactivate_book(db_path, book_id)
    
    return jsonify({ "redirect_url": url_for('books_managment') })

@app.route('/activate_book', methods=["GET", "POST"])
def activate_book():
    status_message_activate_book = "" # Displays the message on website
    
    if request.method == 'POST':
        scanned_code = request.form['activate_book_code']
        status_message_activate_book = activate_book_procedure(scanned_code)
        
    return redirect(url_for("books_managment", status_message_activate_book=status_message_activate_book))

def activate_book_procedure(scanned_code):
    scanned_info = ScannedCodeManagement(scanned_code=scanned_code)
        
    activate_book_info = {
        "ActivationID": scanned_code,
        "ActiveBookID": scanned_info.get_book_id(),
        "isAtTicketNumber": scanned_info.get_ticket_num()
    }
    # The book being activated must already be registered in the system. 
    # So check to make sure that the book being instered is prensent in the system and is not already activated. 
    activate_book_id = activate_book_info["ActiveBookID"]
    if DatabaseQueries.is_book(db=db_path, book_id=activate_book_id) and not(DatabaseQueries.is_activated_book(db=db_path, activated_book_id=activate_book_id)):
        # Active the book
        Database.insert_book_to_ActivatedBook_table(database_path=db_path, active_book_info=activate_book_info)
        return f"Book ({activate_book_id}) has been activated!"
    else:
        return f"Error: Book does not already exist in data base or has already been activated!"

@app.route('/edit_reports')
def edit_reports():
    sales_reports = DatabaseQueries.get_all_sales_reports(db_path)
    
    # Convert to local date and time and filter
    local_reports = []
    filter_date = request.args.get("date")
    filter_time = request.args.get("time")
    
    # convert sales report date and time from utc to local
    for report in sales_reports:
        utc_date = datetime.strptime(report["ReportDate"], "%Y-%m-%d").date()
        utc_time = datetime.strptime(report["ReportTime"], "%H:%M:%S").time()
        local_date = convert_utc_to_local(utc_date, 'America/New_York').strftime("%Y-%m-%d")
        local_time = convert_utc_to_local(utc_time, 'America/New_York').strftime("%I:%M:%S %p")
        
         # Filter logic
        match = True
        if filter_date and local_date != filter_date:
            match = False
        if filter_time and not local_time.startswith(filter_time):
            match = False

        if match:
            report["ReportDate"] = local_date
            report["ReportTime"] = local_time
            local_reports.append(report)
    return render_template("edit_reports.html", sales_reports=local_reports)

@app.route("/edit_report/<report_id>")
def edit_single_report(report_id):
    # Query the sales logs related to this report ID
    sales_logs = DatabaseQueries.get_sales_log(db_path, report_id)
    sale_report = DatabaseQueries.get_daily_report(db_path, report_id)
    # Instant ticket sold recalculation
    instant_tickets_sold_total = calculate_instant_tickets_sold(ReportID=report_id) 
    sale_report["InstantTicketSold"] = instant_tickets_sold_total
    
    # Get the counting order to calc sold
    counting_order = load_config()['ticket_order']
    return render_template("edit_single_report.html", report_id=report_id, sales_logs=sales_logs, sale_report=sale_report, counting_order=counting_order) 

@app.route('/download/<int:report_id>', methods=['POST'])
def download_modified_report(report_id):
    sales_logs = DatabaseQueries.get_sales_log(db_path, report_id)
    sale_report = DatabaseQueries.get_daily_report(db_path, report_id)
    counting_order = load_config()['ticket_order']
    if request.method == "POST":
        create_daily_invoice(report_id)
    return send_file(os.path.join(os.getcwd(), f"invoice_lottery.pdf"), as_attachment=True)
    

if __name__ == '__main__':
    app.run(debug=True)
    
# Check if reportID is the one before next report id or not, if it is then it means that it is a current reportID. TODO: Updating isSOLD?
# If not current reportID then on submit: update that sales log book id and update relative sales logs as well, also redo sales report after this update as well. Update TicketTimeline.
# If current reportID then: update that sales log book id and update relative sales logs as well, also redo sales report after this update as well. Update TicketTimeline. update isAtTicketNumber if closing number was changed.
