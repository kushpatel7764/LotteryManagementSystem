"""
Utility module for handling daily sales reports, invoice creation,
and sales log updates in the lottery database system.
"""

import logging
import os
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

from flask import request, send_file

from lottery_app import generate_invoice
from lottery_app.database import database_queries
from lottery_app.database import update_sale_log, update_sale_report
from lottery_app.email_invoice import email_invoice
from lottery_app.utils.config import db_path, load_config
from lottery_app.utils.error_hanlder import check_error

logger = logging.getLogger(__name__)


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
        database_queries.get_all_instant_tickets_sold_quantity(db_path, report_id),
        msg_data,
        fallback=[],
    )

    result = 0
    for ticket_sold in instant_tickets_sold_quantanties:
        # Ensure `ticketsold` is a dict, fallback to empty dict if not
        if not isinstance(ticket_sold, dict):
            return "ERROR: Invalid ticket sold data", "error"
        ticket_sold_quantity = ticket_sold.get("Ticket_Sold_Quantity", 0)  # pylint: disable=no-member
        ticket_price = ticket_sold.get("TicketPrice", 0)  # pylint: disable=no-member
        try:
            result += ticket_sold_quantity * ticket_price
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
        logger.error("Failed to generate/send invoice: %s", e)
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
    if msg_data["message_type"] == "error":
        return msg_data.get("message"), "error"

    ticket_name = check_error(
        database_queries.get_ticket_name(db_path, game_number), message_holder=msg_data
    )
    if msg_data["message_type"] == "error":
        return msg_data.get("message"), "error"

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
        update_sale_log.insert_sales_log(db_path, sale_log_info),
        message_holder=msg_data,
    )

    return msg_data.get("message", ""), msg_data.get("message_type", "")


def _execute_submit_writes(cursor, daily_totals, next_report_id):
    """
    Execute every database write for a day's submission against a single cursor.

    This function must be called inside an open transaction.  The caller is
    responsible for commit on success and rollback on any exception so that
    all writes succeed together or none of them do.

    Steps (in order):
      1. Insert the daily SaleReport row.
      2. Stamp all Pending SalesLog rows with the real ReportID.
      3. Stamp all Pending TicketTimeline rows with the real ReportID.
      4. Read sold-out books (must happen after step 2 so the JOIN sees the
         newly stamped rows on this same connection).
      5. Remove sold-out books from ActivatedBooks.
      6. Advance isAtTicketNumber to today's closing numbers.
      7. Clear countingTicketNumber for the next day.
    """
    # 1. Insert daily report totals
    update_sale_report.add_daily_totals(cursor, daily_totals)

    # 2. Stamp Pending SalesLog rows
    cursor.execute(
        "UPDATE SalesLog SET ReportID = ? WHERE ReportID = 'Pending'",
        (next_report_id,),
    )

    # 3. Stamp Pending TicketTimeline rows
    cursor.execute(
        "UPDATE TicketTimeLine SET ReportID = ? WHERE ReportID = 'Pending'",
        (next_report_id,),
    )

    # 4. Find sold-out books — readable here because steps 2-3 already ran on
    #    this connection; SQLite surfaces a connection's own uncommitted writes
    #    to subsequent reads on the same connection.
    cursor.execute(
        """
        SELECT SalesLog.ActiveBookID
        FROM SalesLog
        JOIN Books ON SalesLog.ActiveBookID = Books.BookID
        WHERE SalesLog.ReportID = ? AND Books.Is_Sold = 1
        """,
        (next_report_id,),
    )
    sold_book_ids = [row[0] for row in cursor.fetchall()]

    # 5. Deactivate sold-out books
    for book_id in sold_book_ids:
        cursor.execute(
            "DELETE FROM ActivatedBooks WHERE ActiveBookID = ?",
            (book_id,),
        )

    # 6. Advance open-ticket marker to today's closing number
    cursor.execute(
        "UPDATE ActivatedBooks SET isAtTicketNumber = countingTicketNumber"
    )

    # 7. Clear counting numbers ready for tomorrow
    cursor.execute(
        "UPDATE ActivatedBooks SET countingTicketNumber = NULL"
    )


def do_submit_procedure():
    """
    Submit the day's lottery sales in three explicit phases:

    Phase 1 — read-only queries (no writes, no transaction).
    Phase 2 — atomic database transaction: all writes succeed or none do.
    Phase 3 — post-commit side effects: invoice PDF (fatal), email (non-fatal).

    Returns:
        tuple: (message, message_type)
    """
    try:
        # --- Phase 1: read-only setup ---
        next_report_id = database_queries.next_report_id(db_path)
        if isinstance(next_report_id, tuple):
            return next_report_id  # propagate ("error message", "error")

        daily_totals = {
            "ReportID": next_report_id,
            "instant_sold": request.form.get("instant_sold"),
            "online_sold": request.form.get("online_sold"),
            "instant_cashed": request.form.get("instant_cashed"),
            "online_cashed": request.form.get("online_cashed"),
            "cash_on_hand": request.form.get("cash_on_hand"),
        }

        # --- Phase 2: atomic transaction ---
        # A single connection owns every write. On any exception the entire
        # day's submission is rolled back — no partial state is committed.
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            _execute_submit_writes(conn.cursor(), daily_totals, next_report_id)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        # --- Phase 3: post-commit side effects ---
        # Invoice generation reads committed data so it must happen after commit.
        invoice_result = create_daily_invoice(next_report_id)
        if isinstance(invoice_result, tuple) and invoice_result[1] == "error":
            message, status = invoice_result[0], invoice_result[1]
        else:
            # Email is best-effort: a network failure must not surface as a failed
            # submission when all the database work already committed successfully.
            now = datetime.now()
            file_name = f"Invoice#{next_report_id}-{now.strftime('%m-%d-%Y')}.pdf"
            try:
                email_invoice(filename=file_name)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to email invoice: %s", e)
            message, status = "SCANS SUBMITTED SUCCESSFULLY", "success"

        return message, status

    except sqlite3.Error as e:
        traceback.print_exc()
        return f"Database error during submission: {str(e)}", "error"
    except ValueError as ve:
        return str(ve), "error"
    except FileNotFoundError as e:
        return f"Invoice not found: {str(e)}", "error"
    except (TypeError, OSError) as e:
        traceback.print_exc()
        return f"Unexpected error: {str(e)}", "error"
