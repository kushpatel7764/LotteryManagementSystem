"""
Utility module for inserting tickets into the TicketTimeline table.
"""

from lottery_app.database import update_ticket_timeline
from lottery_app.utils.config import db_path
from lottery_app.utils.error_hanlder import check_error

# pylint: disable=too-many-arguments
def insert_ticket(
        scan_id,
        book_id,
        ticket_number,
        ticket_name,
        ticket_price,
        *, # everything after this must be passed by name
        report_id=None):
    """
    Inserts a ticket into the TicketTimeline table.

    Parameters:
        scan_id (str): Unique identifier for the scan.
        book_id (str): ID of the associated book.
        ticket_number (int): Ticket number.
        ticket_name (str): Name of the ticket.
        ticket_price (float): Price of the ticket.
        report_id (str, optional): Associated report ID, if any.

    Returns:
        tuple: A tuple containing:
            - message (str): Status message.
            - message_type (str): Either "success" or "error".
    """
    msg_data = {"message": "", "message_type": ""}
    ticket_info = {
        "ScanID": scan_id,
        "BookID": book_id,
        "TicketNumber": ticket_number,
        "TicketName": ticket_name,
        "TicketPrice": ticket_price,
    }
    if report_id:
        ticket_info["ReportID"] = report_id
    # Insert this ticket in TicketTimeline
    check_error(
        update_ticket_timeline.insert_ticket_to_ticket_timeline_table(db_path, ticket_info),
        message_holder=msg_data,
    )

    return msg_data.get("message", ""), msg_data.get("message_type", "")
