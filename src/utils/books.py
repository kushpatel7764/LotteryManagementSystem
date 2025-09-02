from database import Database, DatabaseQueries
from utils.config import db_path
from utils.error_hanlder import check_error
from ScannedCodeInformationManagement import ScannedCodeManagement
import game_number_lookup_table


def activate_book_procedure(scanned_code):
    msg_data = {"message": "", "message_type": ""}
    try:
        scanned_info = ScannedCodeManagement(scanned_code=scanned_code, db_path=db_path)
        extracted_vals = scanned_info.extract_all_scanned_code()

        if extracted_vals == "INVALID BARCODE":
            return "INVALID BARCODE", "error"  # message, message_type
        # The book being activated must already be registered in the system.
        # So check to make sure that the book being instered is prensent in the
        # system and is not already activated.
        book_exists = DatabaseQueries.is_book(
            db=db_path, book_id=extracted_vals["book_id"]
        )
        book_is_activated = DatabaseQueries.is_activated_book(
            db=db_path, activated_book_id=extracted_vals["book_id"]
        )

        if not book_exists:
            return "BOOK DOES NOT EXISTS IN BOOKS DATABASE!", "error"

        if book_is_activated:
            return "BOOK HAS ALREADY BEEN ACTIVATED!", "error"

        activate_book_info = {
            "ActivationID": scanned_code,
            "ActiveBookID": extracted_vals["book_id"],
            "isAtTicketNumber": extracted_vals["ticket_number"],
        }
        was_active_ticket_num = check_error(
            DatabaseQueries.was_activated(db_path, activate_book_info["ActiveBookID"]),
            msg_data,
            fallback=None,
        )
        # check to see if the book has been activated previosly or not
        if was_active_ticket_num is not None and was_active_ticket_num > -1:
            activate_book_info["isAtTicketNumber"] = was_active_ticket_num

        # Final activation step
        result = check_error(
            Database.insert_book_to_ActivatedBook_table(
                database_path=db_path, active_book_info=activate_book_info
            ),
            message_holder=msg_data,
        )

        # Return error or success response
        if msg_data["message_type"] == "error":
            return msg_data["message"], msg_data["message_type"]
        return result
    except Exception as e:
        return f"Unexpected Error: {str(e)}", "error"


def add_book_procedure(scanned_code):
    scanned_info = ScannedCodeManagement(scanned_code=scanned_code, db_path=db_path)
    extracted_vals = scanned_info.extract_all_scanned_code()

    if extracted_vals == "INVALID BARCODE":
        return "INVALID BARCODE", "error"  # message, message_type
    else:
        # TODO: SHOULD RETURN ERRORS
        lookup_message, lookup_message_type = (
            game_number_lookup_table.insert_new_ticket_name_to_lookup_table(db_path)
        )
        if lookup_message_type == "error":
            # Log or attach a warning, but continue
            warning_message = (
                f"Book added, but TicketName update failed: {lookup_message}"
            )
        else:
            warning_message = None
        book_info = {
            "BookID": extracted_vals["book_id"],
            "GameNumber": extracted_vals["game_number"],
            "Is_Sold": False,
            "BookAmount": extracted_vals["book_amount"],
            "TicketPrice": extracted_vals["ticket_price"],
        }
        book_insert_msg, book_insert_type = Database.insert_book_info_to_Books_table(
            database_path=db_path, book_info=book_info
        )
        # Combine messages if needed
        if warning_message and book_insert_type == "success":
            return warning_message, "error"

        return book_insert_msg, book_insert_type
