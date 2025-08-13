from database import Database
from utils.config import db_path
from utils.error_hanlder import check_error

def insert_ticket(scanID, BookID, TicketNumber, TicketName, TicketPrice, ReportID=None):
    msg_data = {"message": "", "message_type": ""}
    ticket_info = {
        "ScanID": scanID,
        "BookID": BookID,
        "TicketNumber": TicketNumber,
        "TicketName": TicketName,
        "TicketPrice": TicketPrice
    }
    if ReportID:
        ticket_info["ReportID"] = ReportID
    # Insert this ticket in TicketTimeline
    check_error(Database.insert_ticket_to_TicketTimeline_table(db_path, ticket_info), message_holder=msg_data)

    return msg_data.get("message", ""), msg_data.get("message_type", "")