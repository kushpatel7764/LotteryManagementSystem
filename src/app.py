from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from ScannedCodeInformationManagement import ScannedCodeManagement
import Database
import DatabaseQueries
import generate_invoice
import game_number_lookup_table


app = Flask(__name__)
# Feature: Edit lottery, recreate invoice report?
# Feature: Error UI for user
# Issue UTC time database 
# Issue 999

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
    
    return render_template('scan_tickets.html', activated_books=activate_books, instant_tickets_sold_total=instant_tickets_sold_total)

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
    sold = abs(activate_book_isAtTicketNumber[0] - int(lastest_ticket_number))
    sale_log_info = {
        "ActiveBookID": book_id,
        "prev_TicketNum": activate_book_isAtTicketNumber[0], # index 4 is the isAtTicketNumber
        "current_TicketNum": lastest_ticket_number,
        "Ticket_Sold_Quantity": sold,
        "Ticket_Name": DatabaseQueries.get_ticket_name(db_path, game_number),
        "Ticket_GameNumber": game_number
    }
    Database.insert_sales_log(db_path, sale_log_info)
 
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
        "cash_on_hand": request.form.get('cash_on_hand'),
        "total_due": request.form.get('total_due')
    }
    
    # Insert the daily_totals in the Daily_Report Database.
    Database.insert_daily_totals(db_path, daily_totals)
    # Update "Pending" SalesLog ReportID
    Database.update_pending_sales_log_report_id(db_path, next_ReportID)
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
    Database.clear_countingTicketNumber(db_path)

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
    
    

    
if __name__ == '__main__':
    app.run(debug=True)