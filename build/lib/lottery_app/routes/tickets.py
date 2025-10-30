"""
Tickets route for the Lottery Management System.

Handles:
- Scanning tickets for active books.
- Undoing ticket scans.
- Marking books as sold out.
- Submitting the day's sales.
"""


from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import login_required

from lottery_app.database import database_queries
from lottery_app.database import update_activated_books, update_sale_log
from lottery_app.database import update_ticket_timeline, update_books
from lottery_app.scanned_code_information_management import ScannedCodeManagement
from lottery_app.utils.config import db_path, load_config
from lottery_app.utils.error_hanlder import check_error
from lottery_app.utils.reports import (add_sales_log, calculate_instant_tickets_sold,
                           do_submit_procedure)
from lottery_app.utils.tickets import insert_ticket

tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("/scan_tickets", methods=["GET", "POST"])
@login_required
def scan_tickets():
    """
    Route for scanning tickets.
    Validates scanned codes, updates sales logs, and manages ticket states.
    """
    msg_data = {"message": "", "message_type": ""}
    msg_data["message"] = request.args.get("message", "")
    msg_data["message_type"] = request.args.get("message_type", "")
    
    # Display any messages from previous actions
    if msg_data["message_type"] != "" and msg_data["message"] != "":
        flash(msg_data["message"], f"tickets_{msg_data['message_type']}")
        msg_data["message"] = None
        msg_data["message_type"] = None
    
    if request.method == "POST":
        # Get book ids for all the active books
        all_active_book_ids = check_error(
            database_queries.get_all_active_book_ids(
                db=db_path), flash_prefix="tickets")

        # Get relevant information from the scanned code
        scanned_code = request.form["scanned_code"]
        scanned_info = ScannedCodeManagement(
            scanned_code=scanned_code, db_path=db_path)
        extracted_vals = scanned_info.extract_all_scanned_code()

        if extracted_vals == "INVALID BARCODE":
            flash("INVALID BARCODE", f"tickets_error")
        elif extracted_vals["book_id"] not in all_active_book_ids:
            flash("Book IS NOT ACTIVATED! PLEASE ACTIVATE BEFORE SCANNING.", f"tickets_error")
        else:
            # Insert ticket
            scan_id = scanned_code
            msg_data["message"] = "TICKET SCANNED"
            msg_data["message_type"] = "success"
            # check the a ticket for this book_id has not already been scanned
            if check_error(
                database_queries.is_counting_ticket_number_set(
                    db_path, extracted_vals["book_id"]
                ),
                flash_prefix="tickets",
                fallback=False,
            ):
                flash("""A ticket from this book has already been scanned.
                    Please use the UNDO button if you want to rescan.""".upper(), f"tickets_error")
                return _render_scan_tickets()

            ticket_name = check_error(
                database_queries.get_ticket_name(
                    db_path,
                    extracted_vals["game_number"]),
                flash_prefix="tickets",
            )
            check_error(
                insert_ticket(
                    scan_id,
                    extracted_vals["book_id"],
                    extracted_vals["ticket_number"],
                    ticket_name,
                    extracted_vals["ticket_price"],
                ),
                flash_prefix="tickets",
            )
            # Add sales log
            check_error(
                add_sales_log(
                    extracted_vals["book_id"],
                    extracted_vals["ticket_number"],
                    extracted_vals["game_number"],
                ),
                flash_prefix="tickets",
            )
            # Update counting ticket number to show the new change to the user
            check_error(
                update_activated_books.update_counting_ticket_number(
                    db_path,
                    extracted_vals["book_id"],
                    extracted_vals["ticket_number"]),
                flash_prefix="tickets",
            )
    # Get all the active books basically.
    # In reality, making a table to show to the user using activated bookids.
    # Instant ticket sold calculation
    # Get the counting order to calc sold
    # Get activated ticket count
    return _render_scan_tickets()

def _render_scan_tickets():
    """Helper to render the scan tickets page."""
    return render_template(
        "scan_tickets.html",
        activated_books=check_error(
            database_queries.get_scan_ticket_page_table(db=db_path),
            flash_prefix="tickets",
        ),
        instant_tickets_sold_total=check_error(
            calculate_instant_tickets_sold(report_id="Pending"),
            flash_prefix="tickets",
        ),
        counting_order=load_config()["ticket_order"],
        activated_book_count=check_error(
            database_queries.count_activated_books(db_path),
            flash_prefix="tickets",
            fallback=0,
        ),
        should_poll=load_config().get("should_poll", False),
    )


@tickets_bp.route("/undo_scan", methods=["POST"])
@login_required
def undo_scan():
    """
    Route to undo the last scanned ticket for a given book.
    Deletes related logs and resets the book's counting number.
    """
    book_id = request.form.get("book_id")
    msg_data = {"message": "", "message_type": ""}
    if book_id:
        try:
            # Step 1: Delete ticket
            check_error(
                update_ticket_timeline.delete_ticket_timeline_by_book_id(db_path, book_id),
                message_holder=msg_data,
            )

            # Step 2: Delete sales log for that book and TicketTimeLine Log will be
            # deleted automatically
            check_error(
                update_sale_log.delete_sales_log_by_book_id(db_path, book_id),
                message_holder=msg_data,
            )
            # Step 3: Clear the counting ticket number
            check_error(
                update_activated_books.clear_counting_ticket_number(db_path, book_id),
                message_holder=msg_data,
            )
            # Step 4: Mark Book Unsold
            check_error(
                update_books.update_is_sold_for_book(db_path, False, book_id),
                message_holder=msg_data,
            )

            msg_data["message"] = "UNDO SCAN SUCCESSFUL"
            msg_data["message_type"] = "success"
        except ValueError as ve:
            msg_data["message"] = str(ve)
            msg_data["message_type"] = "error"
        except Exception as e: # pylint: disable=broad-exception-caught
            msg_data["message"] = f"Unexpected error: {str(e)}"
            msg_data["message_type"] = "error"
            
    if msg_data.get("message"):
        flash(msg_data["message"], f"tickets_{msg_data['message_type']}")
        msg_data["message"] = None

    return redirect(
        url_for(
            "tickets.scan_tickets",
            message=msg_data.get("message", ""),
            message_type=msg_data.get("message_type", ""),
        )
    )


@tickets_bp.route("/book_sold_out", methods=["POST", "GET"])
@login_required
def book_sold_out():
    """
    Marks a book as sold out and updates related database tables.
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        book_id = request.form.get("book_id")
        if not book_id:
            raise ValueError("No Book ID provided.")
        # Step 1: Mark book as sold
        # Tell Database book is sold out - sets it to be removed from activated
        # tickets
        check_error(
            update_books.update_is_sold_for_book(db_path, True, book_id),
            message_holder=msg_data,
        )

        # Step 2: Get book info
        # Update the closing number for book
        book = check_error(
            database_queries.get_book(db_path, book_id), message_holder=msg_data
        )
        game_number = book[1]
        book_amount = book[3]
        ticket_price = book[4]

        config = load_config()
        if config["ticket_order"] == "ascending":
            sold_out_val = book_amount
        elif config["ticket_order"] == "descending":
            sold_out_val = -1
        else:
            raise ValueError("Invalid ticket_order in config")

        # Step 4: Update counting ticket number
        check_error(
            update_activated_books.update_counting_ticket_number(
                db_path,
                book_id,
                sold_out_val),
            message_holder=msg_data,
        )

        # Step 5: Add ticket timeline entry
        ticket_name = check_error(
            database_queries.get_ticket_name(db_path, game_number),
            message_holder=msg_data,
        )
        # -----TicketNumber 998 in scannID means BookSoldOut.
        scan_id = f"{game_number}{book_id}998{ticket_price}{book_amount}"
        # A Integrety error from insert_ticket implies duplicate insertion which
        # is ok here because of the undo button.
        check_error(
            insert_ticket(scan_id, book_id, -1, ticket_name, ticket_price),
            message_holder=msg_data,
        )

        # Step 6: Add sales log
        # TicketNumber is sold_out_val here
        check_error(
            add_sales_log(
                book_id,
                sold_out_val,
                game_number),
            message_holder=msg_data)

        msg_data["message"] = "BOOK MARKED AS SOLD OUT"
        msg_data["message_type"] = "success"
    except ValueError as ve:
        msg_data["message"] = str(ve)
        msg_data["message_type"] = "error"
    except Exception as e: # pylint: disable=broad-exception-caught
        msg_data["message"] = "Unexpected Error: ".upper() + f"{str(e)}"
        msg_data["message_type"] = "error"
    return redirect(
        url_for(
            "tickets.scan_tickets",
            message=msg_data.get("message", ""),
            message_type=msg_data.get("message_type", ""),
        )
    )


@tickets_bp.route("/submit", methods=["GET", "POST"])
@login_required
def submit():
    """
    Submits the day's ticket sales if submission is allowed.
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        if check_error(
                database_queries.can_submit(db_path),
                msg_data,
                fallback=False):
            result = do_submit_procedure()
            # In case result is an error message
            if isinstance(result, tuple) and result[1] == "error":
                msg_data["message"] = result[0]
                msg_data["message_type"] = result[1]
        # Redirect with message if any
        if msg_data["message"]:
            return redirect(url_for("tickets.scan_tickets", **msg_data))

        return redirect(url_for("tickets.scan_tickets"))

    except ValueError as e:
        return redirect(
            url_for(
                "tickets.scan_tickets",
                message=str(e),
                message_type="error"))
