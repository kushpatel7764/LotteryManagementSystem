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

@app.route('/scan_tickets.html', methods=["GET", "POST"])
def scan_tickets():
    activate_books = DatabaseQueries.get_activated_books(db=db_path)
    return render_template('scan_tickets.html', activated_books=activate_books)

@app.route('/')
def home():
    # While loading the home page initalize the database. 
    Database.initialize_database(db_path)
    return render_template('index.html')

@app.route('/books_managment', methods=["GET", "POST"])
def books_managment():
    if request.method == 'POST':
        scanned_code = request.form['add_book_code']
        add_book_procedure(scanned_code)
    
    # Books info for the books table to display on screen 
    books = DatabaseQueries.get_books(db=db_path)

    return render_template('books_managment.html', books=books)

def add_book_procedure(scanned_code):
    scanned_info = ScannedCodeManagement(scanned_code=scanned_code)
    book_info = {
        "BookID": scanned_info.get_book_id(),
        "GameNumber": scanned_info.get_game_num(),
        "BookAmount": scanned_info.get_book_amount()
    }
    # ticket_info = {
    #     "TicketNumber": scanned_info.get_ticket_num(),
    #     "BookID": scanned_info.get_book_id(),
    #     "TicketName" : "N/A",
    #     "TicketPrice": scanned_info.get_ticket_price()
    # } 
    Database.insert_book_info_to_Books_table(database_path=db_path, book_info=book_info)
    # Database.insert_ticket_to_TicketTimeline_table(database_path=db_path, ticket_info=ticket_info)
    

@app.route('/activate_book', methods=["GET", "POST"])
def activate_book():
    if request.method == 'POST':
        scanned_code = request.form['activate_book_code']
        activate_book_procedure(scanned_code)
        
    # Books info for the books table to display on screen 
    books = DatabaseQueries.get_books(db=db_path)

    return render_template('books_managment.html', books=books)

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
    
    
    


if __name__ == '__main__':
    app.run(debug=True)