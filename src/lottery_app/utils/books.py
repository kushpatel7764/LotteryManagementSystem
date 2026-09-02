"""
Utility module for handling book activation and insertion procedures
in the lottery management system.
"""

import uuid

from lottery_app import game_number_lookup_table
from lottery_app.database import database_queries, update_activated_books, update_books
from lottery_app.scanned_code_information_management import ScannedCodeManagement
from lottery_app.utils.config import db_path, get_boxes, load_config
from lottery_app.utils.error_hanlder import check_error


def activate_book_procedure(scanned_code, box_number=None):
    """
    Activates a book by verifying its existence and adding it to the ActivatedBooks table.

    Args:
        scanned_code (str): The scanned barcode representing the book.
        box_number (str, optional): The physical box the book is being placed in.

    Returns:
        tuple: (message or result, message_type)
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        scanned_info = ScannedCodeManagement(scanned_code=scanned_code, db_path=db_path)
        extracted_vals = scanned_info.extract_all_scanned_code()

        if extracted_vals == "INVALID BARCODE":
            return "INVALID BARCODE", "error"  # message, message_type
        # The book being activated must already be registered in the system.
        # So check to make sure that the book being instered is prensent in the
        # system and is not already activated.
        book_exists = database_queries.is_book(
            db=db_path, book_id=extracted_vals["book_id"]
        )
        book_is_activated = database_queries.is_activated_book(
            db=db_path, activated_book_id=extracted_vals["book_id"]
        )

        if not book_exists:
            return "BOOK DOES NOT EXISTS IN BOOKS DATABASE!", "error"

        if book_is_activated:
            return "BOOK HAS ALREADY BEEN ACTIVATED!", "error"

        if check_error(
            database_queries.is_book_sold(db_path, extracted_vals["book_id"]),
            msg_data,
            fallback=False,
        ):
            return "BOOK HAS BEEN SOLD OUT AND CANNOT BE REACTIVATED!", "error"

        activate_book_info = {
            "ActivationID": scanned_code,
            "ActiveBookID": extracted_vals["book_id"],
            "isAtTicketNumber": extracted_vals["ticket_number"],
            "BoxNumber": box_number or None,
        }
        was_active_ticket_num = check_error(
            database_queries.was_activated(db_path, activate_book_info["ActiveBookID"]),
            msg_data,
            fallback=None,
        )
        # check to see if the book has been activated previosly or not
        if was_active_ticket_num is not None and was_active_ticket_num > -1:
            activate_book_info["isAtTicketNumber"] = was_active_ticket_num

        # Final activation step
        check_error(
            result_or_callable=update_activated_books.insert_book_to_activated_book_table(
                database_path=db_path, active_book_info=activate_book_info
            ),
            message_holder=msg_data,
        )

        return msg_data["message"], msg_data["message_type"]

    except Exception as e:  # pylint: disable=broad-exception-caught
        return f"Unexpected Error: {str(e)}", "error"


def activate_book_by_id_procedure(book_id, box_number=None):
    """
    Activates a book directly by its BookID, without requiring a barcode scan.

    Used for manual activation from the books management table, where the
    book's identity is already known and there is no scanned ticket number
    to read the starting count from.

    Args:
        book_id (str): The BookID to activate.
        box_number (str, optional): The physical box the book is being placed in.

    Returns:
        tuple: (message, message_type)
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        if not book_id:
            return "NO BOOK ID PROVIDED.", "error"

        book_exists = database_queries.is_book(db=db_path, book_id=book_id)
        book_is_activated = database_queries.is_activated_book(
            db=db_path, activated_book_id=book_id
        )

        if not book_exists:
            return "BOOK DOES NOT EXISTS IN BOOKS DATABASE!", "error"

        if book_is_activated:
            return "BOOK HAS ALREADY BEEN ACTIVATED!", "error"

        book = check_error(
            database_queries.get_book(db_path, book_id), message_holder=msg_data
        )
        if msg_data["message_type"] == "error":
            return msg_data["message"], "error"

        if book[2]:
            return "BOOK HAS BEEN SOLD OUT AND CANNOT BE REACTIVATED!", "error"

        book_amount = book[3]

        # No barcode was scanned, so there is no ticket number to read the
        # starting count from. Start the book at the beginning of its range.
        config = load_config()
        if config["ticket_order"] == "ascending":
            starting_ticket_number = 0
        elif config["ticket_order"] == "descending":
            starting_ticket_number = book_amount - 1
        else:
            return "INVALID TICKET_ORDER IN CONFIG", "error"

        activate_book_info = {
            "ActivationID": f"MANUAL-{book_id}-{uuid.uuid4().hex}",
            "ActiveBookID": book_id,
            "isAtTicketNumber": starting_ticket_number,
            "BoxNumber": box_number or None,
        }
        was_active_ticket_num = check_error(
            database_queries.was_activated(db_path, book_id),
            msg_data,
            fallback=None,
        )
        # If the book was activated and used before, resume from where it
        # left off instead of resetting to the start of its range.
        if was_active_ticket_num is not None and was_active_ticket_num > -1:
            activate_book_info["isAtTicketNumber"] = was_active_ticket_num

        check_error(
            result_or_callable=update_activated_books.insert_book_to_activated_book_table(
                database_path=db_path, active_book_info=activate_book_info
            ),
            message_holder=msg_data,
        )

        return msg_data["message"], msg_data["message_type"]

    except Exception as e:  # pylint: disable=broad-exception-caught
        return f"Unexpected Error: {str(e)}", "error"


def add_book_procedure(scanned_code):
    """
    Adds a new book to the Books table and updates the lookup table if needed.

    Args:
        scanned_code (str): The scanned barcode representing the book.

    Returns:
        tuple: (message, message_type)
    """
    scanned_info = ScannedCodeManagement(scanned_code=scanned_code, db_path=db_path)
    extracted_vals = scanned_info.extract_all_scanned_code()

    if extracted_vals == "INVALID BARCODE":
        return "INVALID BARCODE", "error"  # message, message_type

    lookup_message, lookup_message_type = (
        game_number_lookup_table.insert_new_ticket_name_to_lookup_table(db_path)
    )
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
        "TicketPrice": extracted_vals["ticket_price"],
    }
    book_insert_msg, book_insert_type = update_books.insert_book_info_to_books_table(
        database_path=db_path, book_info=book_info
    )
    # Combine messages if needed
    if warning_message and book_insert_type == "success":
        return warning_message, "warning"

    return book_insert_msg, book_insert_type


def suggest_next_empty_box():
    """
    Returns the lowest-numbered configured box that currently has no open
    books in it, or None if every box is occupied (or none are configured).
    """
    boxes = get_boxes()
    if not boxes:
        return None

    occupied = check_error(
        database_queries.get_occupied_box_numbers(db_path), fallback=set()
    )
    for box in sorted(boxes, key=int):
        if box not in occupied:
            return box
    return None
