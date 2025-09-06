"""
Routes for managing lottery sales reports, including editing,
updating, and downloading reports, as well as managing sales logs.
"""


from datetime import datetime

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   url_for)

from src.database import database_queries
from src.database import (update_activated_books, update_books, update_sale_log,
                          update_sale_report, update_ticket_timeline)
from src.utc_to_local_time import convert_utc_to_local
from src.utils.config import db_path, load_config
from src.utils.error_hanlder import check_error
from src.utils.reports import calculate_instant_tickets_sold, create_daily_invoice
from src.utils.tickets import insert_ticket

report_bp = Blueprint("reports", __name__)


@report_bp.route("/edit_reports", methods=["GET", "POST"])
def edit_reports():
    """
    Display all sales reports with optional filtering by date and time.
    Converts UTC to local time and gracefully handles errors.
    """
    # Safely load all reports
    msg_data = {"message": "", "message_type": ""}
    sales_reports = check_error(
        database_queries.get_all_sales_reports(db_path), msg_data, fallback=[]
    )
    # Ensure it's always a list
    if not isinstance(sales_reports, list):
        return render_template(
            "edit_reports.html",
            sales_reports=[],
            message=msg_data.get("message", ""),
            message_type=msg_data.get("message_type", ""),
        )
    # Convert to local date and time and filter
    local_reports = []
    filter_date = request.args.get("date")

    filter_time = None
    filter_time_military = request.args.get("time")
    if filter_time_military:
        try:
            filter_time_obj = datetime.strptime(filter_time_military, "%H:%M")
            # Format to regular time with AM/PM
            filter_time = filter_time_obj.strftime("%I:%M %p")
        except ValueError:
            msg_data["message"] = (
                "Invalid time format. Please use HH:MM (24-hour format)."
            )
            msg_data["message_type"] = "error"
            filter_time = None  # Fail gracefully

    # convert sales report date and time from utc to local
    for report in sales_reports:
        try:
            if not isinstance(report, dict):
                raise ValueError("Invalid report data format")
            utc_date = datetime.strptime(
                report.get("ReportDate"), "%Y-%m-%d").date()
            utc_time = datetime.strptime(
                report.get("ReportTime"), "%H:%M:%S").time()
            local_date = convert_utc_to_local(
                utc_date, "America/New_York").strftime("%Y-%m-%d")
            local_time = convert_utc_to_local(
                utc_time, "America/New_York").strftime("%I:%M %p")
            # Filter logic
            match = True
            if filter_date:
                if local_date != filter_date:
                    match = False
            if filter_time:
                if not local_time.startswith(filter_time):
                    match = False

            if match:
                report["ReportDate"] = local_date
                report["ReportTime"] = local_time
                local_reports.append(report)
        except (KeyError, ValueError, TypeError) as e:
            msg_data["message"] = f"Skipping report due to error: {e}"
            msg_data["message_type"] = "error"
            continue
    return render_template(
        "edit_reports.html",
        sales_reports=local_reports,
        message=msg_data.get("message", ""),
        message_type=msg_data.get("message_type", ""),
    )


@report_bp.route(
    "/edit_report/<report_id>", methods=["GET", "POST"]
)
def edit_single_report(report_id):
    """
    Display a single sales report with all related sales logs.
    Also calculates instant tickets sold for display.
    """
    message = request.args.get("message", "")
    message_type = request.args.get("message_type", "")

    msg_data = {"message": message, "message_type": message_type}
    # Query the sales logs related to this report ID
    sales_logs = check_error(
        database_queries.get_sales_log(db_path, report_id),
        message_holder=msg_data,
        fallback=[],
    )
    sale_report = check_error(
        database_queries.get_daily_report(db_path, report_id),
        message_holder=msg_data,
        fallback={},
    )
    # Instant ticket sold recalculation
    if sale_report:
        instant_tickets_sold_total = check_error(
            calculate_instant_tickets_sold(
                report_id=report_id), msg_data, fallback=0)
        sale_report["InstantTicketSold"] = instant_tickets_sold_total
    # Get the counting order to calc sold
    counting_order = load_config()["ticket_order"]
    return render_template(
        "edit_single_report.html",
        report_id=report_id,
        sales_logs=sales_logs,
        sale_report=sale_report,
        counting_order=counting_order,
        message=message,
        message_type=message_type,
    )

def _get_latest_report_id(msg_data):
    """Helper to fetch the latest report ID safely."""
    return int(check_error(lambda: database_queries.next_report_id(db_path), msg_data)) - 1


def _create_scan_id(game_number, book_id, ticket_num, ticket_price, book_amount):
    """Helper to generate a unique scan ID string."""
    return f"{game_number}{book_id}{ticket_num}{ticket_price}{book_amount}"

@report_bp.route("/update_salesLog", methods=["GET", "POST"])
def update_sales_log():
    """
    Update sales log entries for a given book and report.
    Handles previous, current, and next reports along with ticket timelines.
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        data = request.get_json()
        book_id = data.get("bookID")
        report_id = data.get("reportID")  # str type
        open_ticket = data.get("open")
        close_ticket = data.get("close")

        report_id_int = int(report_id)
        # previous_report_id = report_id_int - 1
        next_report_id = report_id_int + 1
        latest_report_id = _get_latest_report_id(msg_data)
        game_number, book, _ = _get_book_metadata(book_id, msg_data)
        book_info = { # book[4] is ticket price, book[3] is book amount
            "book_id": book_id,
            "game_number": game_number,
            "ticket_price": book[4],
            "scan_id": _create_scan_id(game_number, book_id, close_ticket, book[4], book[3]),
        }
        is_book_sold = check_error(
            database_queries.is_sold(
                db_path, book_id), msg_data)

        # Main update for current report
        _update_current_report(report_id, book_id, open_ticket, close_ticket, msg_data)

        # Book is sold and user now closes it (removing sold status)
        if is_book_sold and close_ticket != "-1":
            _handle_sold_book_reactivation(book_info, report_id_int, latest_report_id, close_ticket,
                                           msg_data)

        # Update previous report if it exists
        if (report_id_int - 1) >= 1: # previous report exists
            _update_previous_report(report_id_int - 1, book_id, open_ticket, msg_data)

        # Update next report if it exists
        if next_report_id <= latest_report_id:
            _update_next_report(next_report_id, book_id, close_ticket, msg_data)

        # If current is the latest report, update isAtTicketNumber
        if latest_report_id == report_id_int:
            check_error(
                update_activated_books.update_is_at_ticketnumber_val(
                    db_path, book_id, close_ticket), msg_data)
        # Update ticket timeline and instant sold for current
        # A update in sale log means the instant sold should also be updated
        _update_ticket_timeline_and_sold(report_id, book_id, close_ticket, msg_data)

        return jsonify(
            {
                "redirect_url": url_for(
                    "reports.edit_single_report",
                    report_id=report_id,
                    message=msg_data.get("message", ""),
                    message_type=msg_data.get("message_type", ""),
                )
            }
        )
    except (KeyError, ValueError, TypeError) as e:
        msg_data["message"] = str(e)
        msg_data["message_type"] = "error"
        safe_report_id = report_id if "report_id" in locals() else "unknown"
        return jsonify(
            {
                "redirect_url": url_for(
                    "reports.edit_single_report",
                    report_id=safe_report_id,
                    message=str(e),
                    message_type="error",
                )
            }
        )


def _update_current_report(report_id, book_id, open_ticket, close_ticket, msg_data):
    """Helper function that applies updates to the current report sales log."""
    check_error(update_sale_log.update_sales_log_prev_ticketnum(
        db_path, open_ticket, report_id, book_id
    ), msg_data)
    check_error(update_sale_log.update_sales_log_current_ticketnum(
        db_path, close_ticket, report_id, book_id
    ), msg_data)


def _update_previous_report(prev_id, book_id, open_ticket, msg_data):
    """Update previous report's ticket timeline and instant sold."""
    check_error(update_ticket_timeline.update_ticket_timeline_ticketnumber(
        db_path, prev_id, book_id, open_ticket
    ), msg_data)
    check_error(update_sale_log.update_sales_log_current_ticketnum(
        db_path, open_ticket, prev_id, book_id
    ), msg_data)
    prev_instant_sold = check_error(calculate_instant_tickets_sold(prev_id), msg_data)
    check_error(update_sale_report.update_sale_report_instant_sold(
        db_path, prev_instant_sold, prev_id
    ), msg_data)


def _update_next_report(next_id, book_id, close_ticket, msg_data):
    """Update next report's ticket timeline and instant sold."""
    check_error(update_sale_log.update_sales_log_prev_ticketnum(
        db_path, close_ticket, next_id, book_id
    ), msg_data)
    next_instant_sold = check_error(calculate_instant_tickets_sold(next_id), msg_data)
    check_error(update_sale_report.update_sale_report_instant_sold(
        db_path, next_instant_sold, next_id
    ), msg_data)


def _update_ticket_timeline_and_sold(report_id, book_id, close_ticket, msg_data):
    """Update instant sold and ticket timeline for the current report."""
    instant_sold = check_error(calculate_instant_tickets_sold(report_id), msg_data)
    check_error(update_sale_report.update_sale_report_instant_sold(
        db_path, instant_sold, report_id
    ), msg_data)
    check_error(update_ticket_timeline.update_ticket_timeline_ticketnumber(
        db_path, report_id, book_id, close_ticket
    ), msg_data)


def _get_book_metadata(book_id, msg_data):
    """Fetch essential book data (game number, book details, ticket name)."""
    game_number = check_error(database_queries.get_game_num_of(db_path, book_id), msg_data)
    book = check_error(database_queries.get_book(db_path, book_id), msg_data)
    ticket_name = check_error(database_queries.get_ticket_name(db_path, game_number), msg_data)
    return game_number, book, ticket_name


def _handle_sold_book_reactivation(book_info, report_id_int, latest_report_id, close_ticket_num,
                                    msg_data):
    """
    Helper to handle reactivation of books previously marked as sold.
    Updates subsequent reports, sales logs, tickets, and reactivates the book.
    book_info: dict with keys: book_id, game_number, ticket_price, scan_id
    """

    book_id = book_info["book_id"]
    game_number = book_info["game_number"]
    ticket_price = book_info["ticket_price"]
    scan_id = book_info["scan_id"]
    # Mark book as not sold
    check_error(update_books.update_is_sold_for_book(db_path, False, book_id), msg_data)

    for rid in range(report_id_int + 1, latest_report_id + 1):
        ticket_name = check_error(database_queries.get_ticket_name(db_path, game_number), msg_data)
        sale_log_info = {
            "ReportID": str(rid),
            "ActiveBookID": book_id,
            "prev_TicketNum": close_ticket_num,
            "current_TicketNum": close_ticket_num,
            "Ticket_Name": ticket_name,
            "Ticket_GameNumber": game_number,
        }
        check_error(update_sale_log.insert_sales_log(db_path, sale_log_info), msg_data)

        instant_sold = check_error(calculate_instant_tickets_sold(rid), msg_data)
        check_error(update_sale_report.update_sale_report_instant_sold(db_path, instant_sold, rid),
                    msg_data)

        check_error(insert_ticket(scan_id, book_id, close_ticket_num, ticket_name, ticket_price,
                                  report_id=str(rid)), msg_data)

    activate_book_info = {
        "ActivationID": scan_id,
        "ActiveBookID": book_id,
        "isAtTicketNumber": close_ticket_num,
    }
    check_error(update_activated_books.insert_book_to_activated_book_table(db_path,
                                                                activate_book_info), msg_data)


@report_bp.route("/update_sale_report/<report_id>", methods=["GET", "POST"])
def update_sale_reports(report_id):
    """
    Update the summary sale report values for a given report.
    """
    msg_data = {"message": "", "message_type": ""}
    try:
        if request.method == "POST":
            instant_sold = request.form["instant_sold"]
            online_sold = request.form["online_sold"]
            instant_cashed = request.form["instant_cashed"]
            online_cashed = request.form["online_cashed"]
            cash_on_hand = request.form["cash_on_hand"]

            check_error(
                update_sale_report.update_sale_report(
                    db_path,
                    instant_sold,
                    online_sold,
                    instant_cashed,
                    online_cashed,
                    cash_on_hand=cash_on_hand,
                    report_id=report_id,
                ),
                message_holder=msg_data,
            )
        return redirect(
            url_for(
                "reports.edit_single_report",
                report_id=report_id,
                message=msg_data.get("message", ""),
                message_type=msg_data.get("message_type", ""),
            )
        )
    except ValueError as e:
        return redirect(
            url_for(
                "reports.edit_single_report",
                report_id=report_id,
                message=str(e),
                message_type="error",
            )
        )


@report_bp.route(
    "/download/<int:report_id>", methods=["GET"]
)  # change to GET for easier triggering
def download_modified_report(report_id):
    """
    Trigger the download of the daily invoice report for a given report ID.
    """
    msg_data = {"message": "", "message_type": ""}
    result = check_error(lambda: create_daily_invoice(report_id), msg_data)

    if msg_data.get("message_type") == "error":
        return msg_data["message"], msg_data["message_type"]

    return result
