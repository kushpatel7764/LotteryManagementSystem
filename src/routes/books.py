from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from database import Database, DatabaseQueries
from utils.config import db_path 
from utils.error_hanlder import check_error
from utils.books import activate_book_procedure, add_book_procedure

books_bp = Blueprint('books', __name__)

@books_bp.route('/books_managment', methods=["GET", "POST"])
def books_managment():
    msg_data = {"message": request.args.get('message', ''), "message_type": request.args.get('message_type', '')}
    # The redirect from /activate will generate a URL like: 
    # /books_managment?activate_book_message=SomeMessage&activate_book_message_type=success
    # request.args.get('activate_book_message', '') will then get these arguments
    
    if request.method == 'POST':
        scanned_code = request.form['add_book_code']
        add_result = check_error(lambda: add_book_procedure(scanned_code), msg_data)
        if isinstance(add_result, tuple) and add_result[1] == "error":
            msg_data["message"], msg_data["message_type"] = add_result
            
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
    
    return render_template( 
        "books_managment.html",
        books=books,
        activated_ids=activated_ids,
        message=msg_data.get("message", ""),
        message_type=msg_data.get("message_type", "")
    )
    
@books_bp.route('/delete_book', methods=['POST', 'GET'])
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
                "redirect_url": url_for('books.books_managment'),
                "message": msg_data["message"],
                "message_type": msg_data["message_type"]
            }), 500

        
        return jsonify({ "redirect_url": url_for('books.books_managment'),
                        "message": f"Book {book_id} deleted successfully.",
                        "message_type": "success"})
    except Exception as e:
        print(f"Error deleting book {book_id}: {e}")
        return jsonify({
            "redirect_url": url_for('books.books_managment'),
            "message": f"Error deleting book: {str(e)}",
            "message_type": "error"
        }), 500

@books_bp.route('/deactivate_book', methods=['POST', 'GET'])
def deactivate_book():
    msg_data = {"message": "", "message_type": ""}
    try:
        data = request.get_json()
        book_id = data.get('bookID')
        print(f"Deactivating: {book_id}")
        
        check_error(Database.deactivate_book(db_path, book_id), msg_data)
        if msg_data["message_type"] == "error":
            return jsonify({
                "redirect_url": url_for('books.books_managment'),
                "message": msg_data["message"],
                "message_type": msg_data["message_type"]
            }), 500
        return jsonify({ "redirect_url": url_for('books.books_managment') })
    except Exception as e:
        print(f"Unexpected error while deactivating book {book_id}: {e}")
        return jsonify({
            "redirect_url": url_for('books.books_managment'),
            "message": f"Unexpected error deactivating book: {e}",
            "message_type": "error"
        }), 500
    

@books_bp.route('/activate_book', methods=["GET", "POST"])
def activate_book():
    message = ""
    message_type = ""
    
    if request.method == 'POST':
        scanned_code = request.form.get('activate_book_code')
        message, message_type = activate_book_procedure(scanned_code) 
        
    return redirect(url_for("books.books_managment", message=message, message_type=message_type))

