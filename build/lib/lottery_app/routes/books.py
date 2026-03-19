"""
Books management routes.

This module provides routes for managing books, including listing,
adding, activating, deactivating, and deleting books in the system.
"""

import sqlite3
from flask import Blueprint, jsonify, redirect, render_template, request, url_for, flash
from flask_login import login_required

from lottery_app.database import database_queries
from lottery_app.database import update_books, update_activated_books
from lottery_app.utils.books import activate_book_procedure, add_book_procedure
from lottery_app.utils.config import db_path, load_config
from lottery_app.utils.error_hanlder import check_error


books_bp = Blueprint("books", __name__)


@books_bp.route("/books_managment", methods=["GET", "POST"])
@login_required
def books_managment():
    """
    Display and manage books.

    Handles both GET and POST:
    - GET: Renders the book management page.
    - POST: Adds a new book using the scanned code.
    """
    msg_data = {
        "message": request.args.get("message", ""),
        "message_type": request.args.get("message_type", ""),
    }

    if msg_data["message_type"] != "" and msg_data["message"] != "":
        flash(msg_data["message"], f"books_{msg_data['message_type']}")
        msg_data["message"] = None
        msg_data["message_type"] = None

    # The redirect from /activate will generate a URL like:
    # /books_managment?activate_book_message=SomeMessage&activate_book_message_type=success
    # request.args.get('activate_book_message', '') will then get these
    # arguments

    if request.method == "POST":
        scanned_code = request.form["add_book_code"]

        check_error(add_book_procedure(scanned_code), flash_prefix="books")

    # Books info for the books table to display on screen
    books_result = check_error(
        database_queries.get_books(db=db_path), flash_prefix="books", fallback=[]
    )

    books = books_result if isinstance(books_result, list) else []

    # Setting TicketNames
    if books:
        for book in books:
            if isinstance(book, dict):
                # pylint: disable=unsupported-assignment-operation
                game_number = book.get("GameNumber")
                book["TicketName"] = check_error(
                    database_queries.get_ticket_name(db_path, game_number),
                    fallback="N/A",
                    flash_prefix="books",
                )

    # Get activated books (just the BookIDs)
    activated_books = check_error(
        database_queries.get_activated_books(db_path), flash_prefix="books", fallback=[]
    )  # should return a list of dicts or a list of IDs
    activated_ids = set()
    for book in activated_books:
        if isinstance(book, dict):
            activated_ids.add(book.get("ActiveBookID"))

    should_poll = load_config().get("should_poll", False)

    return render_template(
        "books_managment.html",
        books=books,
        activated_ids=activated_ids,
        should_poll=should_poll,
    )


@books_bp.route("/delete_book", methods=["POST", "GET"])
@login_required
def delete_book():
    """
    Deletes a book after deactivating it.

    Expects JSON data with a 'bookID' field.
    Returns a JSON response with redirect URL, message, and status.
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        data = request.get_json()
        if not data or "bookID" not in data:
            raise ValueError("Missing 'bookID' in request data.")
        book_id = data.get("bookID")
        print(f"Deleting: {book_id}")
        # Deactivate first, then delete
        # Safely run deactivation and deletion with error checking
        check_error(
            lambda: update_activated_books.deactivate_book(db_path, book_id), msg_data
        )
        check_error(lambda: update_books.delete_book(db_path, book_id), msg_data)

        if msg_data["message_type"] == "error":
            return jsonify(
                {
                    "redirect_url": url_for("books.books_managment"),
                    "message": msg_data["message"],
                    "message_type": msg_data["message_type"],
                }
            ), 500

        return jsonify(
            {
                "redirect_url": url_for("books.books_managment"),
                "message": f"Book {book_id} deleted successfully.",
                "message_type": "success",
            }
        )
    except (ValueError, KeyError, TypeError) as e:
        # Handle invalid request or missing keys
        return (
            jsonify(
                {
                    "redirect_url": url_for("books.books_managment"),
                    "message": f"Invalid request: {str(e)}",
                    "message_type": "error",
                }
            ),
            400,
        )
    except (RuntimeError, sqlite3.Error) as e:
        # Handle database or runtime errors
        return (
            jsonify(
                {
                    "redirect_url": url_for("books.books_managment"),
                    "message": f"Database or runtime error: {str(e)}",
                    "message_type": "error",
                }
            ),
            500,
        )


@books_bp.route("/deactivate_book", methods=["POST", "GET"])
@login_required
def deactivate_book():
    """
    Deactivate a book by its ID.

    Expects JSON data with a 'bookID' field.
    Returns a JSON response with redirect URL and status message.
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        data = request.get_json()
        book_id = data.get("bookID")

        check_error(update_activated_books.deactivate_book(db_path, book_id), msg_data)
        if msg_data["message_type"] == "error":
            return jsonify(
                {
                    "redirect_url": url_for("books.books_managment"),
                    "message": msg_data["message"],
                    "message_type": msg_data["message_type"],
                }
            ), 500
        return jsonify({"redirect_url": url_for("books.books_managment")})
    except (ValueError, KeyError, TypeError) as e:
        return (
            jsonify(
                {
                    "redirect_url": url_for("books.books_managment"),
                    "message": f"Invalid request: {e}",
                    "message_type": "error",
                }
            ),
            400,
        )
    except sqlite3.Error as e:
        return (
            jsonify(
                {
                    "redirect_url": url_for("books.books_managment"),
                    "message": f"Database error: {e}",
                    "message_type": "error",
                }
            ),
            500,
        )
    except RuntimeError as e:
        return (
            jsonify(
                {
                    "redirect_url": url_for("books.books_managment"),
                    "message": f"Runtime error: {e}",
                    "message_type": "error",
                }
            ),
            500,
        )


@books_bp.route("/activate_book", methods=["GET", "POST"])
@login_required
def activate_book():
    """
    Activate a book by its scanned code.

    Expects a form with 'activate_book_code'.
    """
    message = ""
    message_type = ""

    if request.method == "POST":
        scanned_code = request.form.get("activate_book_code")
        message, message_type = activate_book_procedure(scanned_code)

    return redirect(
        url_for("books.books_managment", message=message, message_type=message_type)
    )
