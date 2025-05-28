from flask import Flask, render_template, request, redirect, url_for
import os
from datetime import datetime
from ScannedCodeInformationManagement import ScannedCodeManagement
import Database
import DatabaseQueries

app = Flask(__name__)

# Get database path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_dir, 'Lottery_Management_Database.db')

@app.route('/scan_tickets', methods=["GET", "POST"])
def scan_tickets():
    # Get all the active books
    activate_books = DatabaseQueries.get_scan_ticket_page_table(db_path=db_path)
    
    if request.method == "POST":
        # Get book ids for all the active books 
        all_active_book_ids = DatabaseQueries.get_all_active_book_ids(db=db_path)
        
        # Get relevant information from the scanned code
        scanned_code = request.form['scanned_code']
        scanned_info = ScannedCodeManagement(scanned_code=scanned_code)
        scanned_book_id = scanned_info.get_book_id()
        
        # If the book id from scanned code is present in the active books then it is valid.
        if scanned_book_id in all_active_book_ids:
            print("Activated Book")
            ticket_info = {
                "ScanID": scanned_code,
                "BookID": scanned_info.get_book_id(),
                "TicketNumber": scanned_info.get_ticket_num(),
                "TicketName": "N/A",
                "TicketPrice": scanned_info.get_ticket_price()
            }
            # Insert this ticket in TicketTimeline
            Database.insert_ticket_to_TicketTimeline_table(db_path, ticket_info)
            # Add the closing number 
            Database.update_counting_ticket_number(db_path, ticket_info['BookID'], ticket_info['TicketNumber'])
            # Add a sales log for this scan
            activate_book_isAtTicketNumber = DatabaseQueries.get_activated_book_isAtTicketNumber(db_path, ticket_info["BookID"])
            # ---- Calulateing sold (999 will change this)
            sold = abs(activate_book_isAtTicketNumber[0] - int(ticket_info["TicketNumber"]))
            scanned_info = {
                "ActiveBookID": ticket_info['BookID'],
                "prev_TicketNum": activate_book_isAtTicketNumber[0], # index 4 is the isAtTicketNumber
                "current_TicketNum": ticket_info["TicketNumber"],
                "Ticket_Sold_Quantity": sold,
                "Ticket_Name": "N/A",
                "Ticket_GameNumber": scanned_info.get_game_num(),
            }
            Database.insert_sales_log(db_path, scanned_info)
            
        else:
            print("UnActivated Book")
    
    return render_template('scan_tickets.html', activated_books=activate_books, add_to_close_number=None)

@app.route("/book_sold_out", methods=["POST"])
def book_sold_out():
    book_id = request.form.get("book_id")
    # Tell Database book is sold out - sets it to be removed from activated tickets
    Database.update_is_sold_for_book(db_path, book_id)
    # Update the closing number for book
    Database.update_counting_ticket_number(db_path, book_id, -1)
    return redirect(url_for("scan_tickets"))  # or your page name


@app.route('/')
def home():
    # While loading the home page initalize the database. 
    Database.initialize_database(db_path)
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

    return render_template('books_managment.html', books=books, status_message_add_book=status_message_add_book)

def add_book_procedure(scanned_code):
    scanned_info = ScannedCodeManagement(scanned_code=scanned_code)
    book_info = {
        "BookID": scanned_info.get_book_id(),
        "GameNumber": scanned_info.get_game_num(),
        "BookAmount": scanned_info.get_book_amount()
    }
    Database.insert_book_info_to_Books_table(database_path=db_path, book_info=book_info)
    

@app.route('/activate_book', methods=["GET", "POST"])
def activate_book():
    status_message_activate_book = "" # Displays the message on website
    
    if request.method == 'POST':
        scanned_code = request.form['activate_book_code']
        status_message_activate_book = activate_book_procedure(scanned_code)
        
    # Books info for the books table to display on screen 
    books = DatabaseQueries.get_books(db=db_path)

    return render_template('books_managment.html', books=books, status_message_activate_book=status_message_activate_book)

def activate_book_procedure(scanned_code):
    scanned_info = ScannedCodeManagement(scanned_code=scanned_code)
    activate_book_info = {
        "ActivationID": scanned_code,
        "ActiveBookID": scanned_info.get_book_id(),
        "Is_Sold": False,
        "isAtTicketNumber": scanned_info.get_ticket_num()
    }
    # The book being activated must already be registered in the system. 
    # So check to make sure that the book being instered is prensent in the system and is not already activated. 
    activate_book_id = activate_book_info["ActiveBookID"]
    if DatabaseQueries.get_book(db=db_path, book_id=activate_book_id) and not(DatabaseQueries.get_activated_book(db=db_path, activated_book_id=activate_book_id)):
        # Active the book
        Database.insert_book_to_ActivatedBook_table(database_path=db_path, active_book_info=activate_book_info)
        return f"Book ({activate_book_id}) has been activated!"
    else:
        return f"Error: Book does not already exist in data base or has already been activated!"
    
    


if __name__ == '__main__':
    app.run(debug=True)