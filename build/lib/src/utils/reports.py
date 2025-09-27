"""
Utility module for handling daily sales reports, invoice creation,
and sales log updates in the lottery database system.
"""

import os
import traceback
from datetime import datetime
from pathlib import Path

from flask import request, send_file

from src import generate_invoice
from src.database import database_queries
from src.database import update_sale_log, update_sale_report
from src.database import update_ticket_timeline, update_activated_books
from src.email_invoice import email_invoice
from src.utils.config import db_path, load_config
from src.utils.error_hanlder import check_error


def calculate_instant_tickets_sold(report_id):
    """
    Calculates the total sales from instant tickets for a given report.

    Parameters:
        report_id (str): The report ID to fetch ticket sales for.

    Returns:
        float: Total sales amount for instant tickets.
        If an error occurs, returns 0 and sets msg_data with error details.
    """
    msg_data = {"message": "", "message_type": ""}
    instant_tickets_sold_quantanties = check_error(
        database_queries.get_all_instant_tickets_sold_quantity(
            db_path, report_id), msg_data, fallback=[], )

    result = 0
    for ticket_sold in instant_tickets_sold_quantanties:
        # Ensure `ticketsold` is a dict, fallback to empty dict if not
        if not isinstance(ticket_sold, dict):
            return "ERROR: Invalid ticket sold data", "error"
        ticket_sold_quantity = ticket_sold.get("Ticket_Sold_Quantity", 0)  # pylint: disable=no-member
        ticket_price = ticket_sold.get("TicketPrice", 0) # pylint: disable=no-member
        try:
            result += ticket_sold_quantity * \
                ticket_price
        except (KeyError, TypeError) as e:
            if msg_data is not None:
                msg_data["message"] = (
                    f"Error calculating instant tickets sold: {str(e)}"
                )
                msg_data["message_type"] = "error"
            return 0
    return result


def create_daily_invoice(report_id, return_path_only=False):
    """
    Creates a daily invoice PDF for a given report.

    Parameters:
        report_id (str): The report ID to generate the invoice for.
        return_path_only (bool): If True, returns only the file path instead of sending.

    Returns:
        tuple: (file_path or send_file response, "success") on success,
               (error_message, "error") on failure.
    """
    msg_data = {"message": "", "message_type": ""}
    config = load_config()
    invoice_log = check_error(
        database_queries.get_table_for_invoice(db_path, report_id), msg_data
    )
    if msg_data.get("message_type") == "error":
        return "ERROR: Unable to get the invoice table", "error"

    store_info = {
        "Business Name": config.get("business_name") or "Store Name",
        "Address": config.get("business_address") or "Store Address",
        "Phone": config.get("business_phone") or "N/a",
        "Email": config.get("business_email") or "N/a",
    }
    daily_report = check_error(
        database_queries.get_daily_report(db_path, report_id), msg_data
    )

    if msg_data.get("message_type") == "error":
        return "ERROR: Unable to create daily invoice", "error"
    output_path = config.get("invoice_output_path")
    # Determine output directory
    if output_path and os.path.isdir(output_path):
        save_dir = output_path
    else:
        save_dir = str(Path.home() / "Downloads")
    now = datetime.now()
    invoice_number = f"{report_id}"
    file_name = f"Invoice#{report_id}-{now.strftime('%m-%d-%Y')}.pdf"
    full_path = os.path.join(save_dir, file_name)
    try:
        generate_invoice.generate_lottery_invoice_pdf(
            full_path, store_info, invoice_log, invoice_number, daily_report
        )

        if return_path_only:
            return full_path, "success"

        return send_file(full_path, as_attachment=True), "success"
    except (ValueError, TypeError, OSError) as e:
        # Log or handle error appropriately
        print(f"Failed to generate/send invoice: {e}")
        return f"Error generating invoice: {e}", 500


def add_sales_log(book_id, lastest_ticket_number, game_number):
    """
    Adds a sales log entry for a given book.

    Parameters:
        book_id (str): Active book ID.
        latest_ticket_number (int): Latest ticket number.
        game_number (str): Game number associated with the ticket.

    Returns:
        tuple: (message, message_type)
    """
    msg_data = {"message": "", "message_type": ""}

    # Get the current state of the book
    activate_book_is_at_ticket_number = check_error(
        database_queries.get_activated_book_is_at_ticketnumber(db_path, book_id),
        message_holder=msg_data,
    )
    ticket_name = check_error(
        database_queries.get_ticket_name(
            db_path,
            game_number),
        message_holder=msg_data)

    # Build sales log entry
    sale_log_info = {
        "ActiveBookID": book_id,
        # index 4 is the isAtTicketNumber
        "prev_TicketNum": activate_book_is_at_ticket_number,
        "current_TicketNum": lastest_ticket_number,
        "Ticket_Name": ticket_name,
        "Ticket_GameNumber": game_number,
    }

    check_error(
        update_sale_log.insert_sales_log(
            db_path,
            sale_log_info),
        message_holder=msg_data)

    return msg_data.get("message", ""), msg_data.get("message_type", "")


def do_submit_procedure():
    """
    Handles the submission procedure for daily lottery sales reporting.
    This includes:
      - Inserting daily totals
      - Updating pending logs
      - Generating invoice
      - Deactivating sold books
      - Updating ticket numbers

    Returns:
        tuple: (message, message_type)
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        next_report_id = check_error(
            database_queries.next_report_id(db_path), msg_data
        )  # STRING
        # Get form values
        daily_totals = {
            "ReportID": next_report_id,
            "instant_sold": request.form.get("instant_sold"),
            "online_sold": request.form.get("online_sold"),
            "instant_cashed": request.form.get("instant_cashed"),
            "online_cashed": request.form.get("online_cashed"),
            "cash_on_hand": request.form.get("cash_on_hand"),
        }

        # Insert the daily_totals in the Daily_Report Database.
        check_error(
            update_sale_report.insert_daily_totals(
                db_path,
                daily_totals),
            msg_data)
        # Update "Pending" SalesLog ReportID
        check_error(
            update_sale_log.update_pending_sales_log_report_id(
                db_path, next_report_id), msg_data, )
        # Update "Pending" TicketTimeLine ReportID
        check_error(
            update_ticket_timeline.update_pending_ticket_timeline_report_id(
                db_path, next_report_id), msg_data, )

        # Create a Invoice
        check_error(create_daily_invoice(next_report_id), msg_data)

        # Remove sold out books from current ActivatedBooks table using there
        # book ids
        sold_out_books = check_error(
            database_queries.get_all_sold_books(
                db_path, next_report_id), msg_data)
        for book in sold_out_books:
            # Ensure `book` is a dict, fallback to empty dict if not
            if not isinstance(book, dict):
                return "ERROR: Invalid book data", "error"
            book_id = book.get("BookID")  # pylint: disable=no-member
            check_error(
                update_activated_books.deactivate_book(
                    db_path,
                    book_id),
                msg_data)
        # Update Database
        # isAtTicketNumber in ActiviatedBooks needs to be set to current numbers from today's scans.
        # countingTicketNumber needs to be set to None since nothing is being
        # counted after submit.
        check_error(update_activated_books.update_is_at_ticketnumbers(db_path), msg_data)
        check_error(update_activated_books.clear_counting_ticket_numbers(db_path), msg_data)
        now = datetime.now()
        file_name = f"Invoice#{next_report_id}-{now.strftime('%m-%d-%Y')}.pdf"
        email_invoice(filename=file_name)

        if msg_data.get("message_type") == "error":
            return msg_data["message"], msg_data["message_type"]
        return "SCANS SUBMITTED SUCCESSFULLY", "success"
    except ValueError as ve:
        return str(ve), "error"
    except FileNotFoundError as fnf:
        return f"Invoice not found: {str(fnf)}", "error"
    except (TypeError, OSError) as e:
        traceback.print_exc()
        return f"Unexpected error: {str(e)}", "error"
