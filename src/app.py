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
    return render_template('scan_tickets.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add_books', methods=["GET", "POST"])
def add_books():
    if request.method == 'POST':
        scanned_code = request.form['scanned_code']
        scanned_info = ScannedCodeManagement(scanned_code=scanned_code)
        book_info = {
            "BookID": scanned_info.get_book_id(),
            "GameNumber": scanned_info.get_game_num(),
            "BookAmount": scanned_info.get_book_amount(),
            "isAtTicketNumber": scanned_info.get_ticket_num(),
        }
        ticket_info = {
            "TicketNumber": scanned_info.get_ticket_num(),
            "BookID": scanned_info.get_book_id(),
            "TicketName" : "N/A",
            "TicketPrice": scanned_info.get_ticket_price()
        }
        Database.insert_book_to_Books_table(database_path=db_path, book_info=book_info)
        Database.insert_ticket_to_TicketTimeline_table(database_path=db_path, ticket_info=ticket_info)
    
    books = DatabaseQueries.get_books(db=db_path)

    return render_template('add_books.html', books=books)

@app.route('/activate_book')
def activate_book():
    return "Book activated successfully. <a href='/'>Return Home</a>"

if __name__ == '__main__':
    app.run(debug=True)