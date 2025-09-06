"""
Database management module for the Ticket Timeline table in lottery database system.
"""

import sqlite3

from src.database.setup_database import initialize_database
from src.decorators import get_db_cursor


def add_ticket_to_timeline(cursor, ticket_info):
    """
    Inserts a ticket record into the tickettimeline table with a "pending" reportID.

    Parameters:
        ticket_info (dict): A dictionary with keys:
            - ScanID
            - BookID
            - TicketNumber
            - TicketName
            - TicketPrice
    """
    cursor.execute(
        """
        INSERT INTO TicketTimeline (ScanID, BookID, TicketNumber, TicketName, TicketPrice)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            ticket_info["ScanID"],
            ticket_info["BookID"],
            ticket_info["TicketNumber"],
            ticket_info["TicketName"],
            ticket_info["TicketPrice"],
        ),
    )


def add_ticket_to_timeline_at_report_id(cursor, ticket_info):
    """
    Inserts a ticket record into the tickettimeline table with a specific reportID.

    Parameters:
        ticket_info (dict): A dictionary with keys:
            - ScanID
            - ReportID
            - BookID
            - TicketNumber
            - TicketName
            - TicketPrice
    """
    cursor.execute(
        """
        INSERT INTO TicketTimeline (ScanID, ReportID, BookID, TicketNumber, TicketName, TicketPrice)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            ticket_info["ScanID"],
            ticket_info["ReportID"],
            ticket_info["BookID"],
            ticket_info["TicketNumber"],
            ticket_info["TicketName"],
            ticket_info["TicketPrice"],
        ),
    )


def insert_ticket_to_ticket_timeline_table(database_path, ticket_info):
    """
    Inserts a ticket record into the 'TicketTimeline' table of the specified SQLite database.

    Parameters:
        database_path (str): The file path to the SQLite database.
        ticket_info (dict): A dictionary containing ticket details.
                            If it includes a "ReportID" key, the ticket will be inserted
                            at the associated report using `add_ticket_to_timeline_at_reportID`.
                            Otherwise, it uses `add_ticket_to_timeline`.

    Returns:
        tuple: A tuple with a message and status type.

    Description:
        This function:
        1. Checks whether a "ReportID" is provided in the `ticket_info`:
           - If yes, it calls `add_ticket_to_timeline_at_reportID` to insert the ticket.
           - If no, it calls `add_ticket_to_timeline`.
        2. Handles and returns error messages for integrity or general SQLite exceptions.
    """
    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            if "ReportID" in ticket_info:
                add_ticket_to_timeline_at_report_id(cursor, ticket_info)
            else:
                add_ticket_to_timeline(cursor, ticket_info)
    except sqlite3.IntegrityError as e:
        return f"INTEGRITY ERROR SETTING TICKET TIMELINE: {e}", "error"
    except sqlite3.Error as e:
        return f"ERROR INSERTING SETTING TICKET TIMELINE: {e}", "error"

    return "TICKET SUCCESSFULLY INSERTED!", "success"


def delete_ticket_timeline_by_book_id(database_path, book_id):
    """
    Deletes ticket entries for a specific book from the TicketTimeLine table
    where the ReportID is marked as 'Pending'.

    Parameters:
        database_path (str): The file path to the SQLite database.
        book_id (str or int): The BookID whose associated pending timeline entries
        should be deleted.

    Returns:
        tuple:
            - ("ERROR DELETING TICKETTIMELINE BOOKID(<book_id>): <error>", "error")
            on failure.
    """

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                "DELETE FROM TicketTimeLine WHERE BookID = ? AND ReportID = 'Pending';",
                (book_id,),
            )
    except sqlite3.Error as e:
        return f"ERROR DELETING TICKETTIMELINE BOOKID({book_id}): {e}", "error"

    return None


def update_pending_ticket_timeline_report_id(database_path, report_id):
    """
    Updates all pending ticket timeline entries by assigning them the specified ReportID.

    Parameters:
        database_path (str): Path to the SQLite database.
        report_id (str): The ReportID to assign to all 'Pending' TicketTimeLine entries.

    Returns:
        tuple:
            - ("ERROR ADDING REPORTID(<report_id>) TO PENDING TICKET TIMELINE ENTRIES:
            <error>", "error") on SQLite error.

    Description:
        This function finds all rows in the TicketTimeLine table where the ReportID is
        currently 'Pending'and updates them with the specified ReportID, during report
        finalization.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
            UPDATE TicketTimeLine
            SET ReportID = ?
            WHERE ReportID = 'Pending';
            """,
                (report_id,),
            )
    except sqlite3.Error as e:
        return (
            f"Error adding reportID({report_id}) to pending ticket timeline entires: ".upper() +
            f"{e}",
            "error",
        )

    return None


def update_ticket_timeline_ticketnumber(
        database_path, report_id, book_id, ticketnumber):
    """
    Updates the TicketNumber for a specific entry in the TicketTimeLine table.

    Parameters:
        database_path (str): Path to the SQLite database.
        reportID (str or int): The ReportID identifying the timeline entry.
        bookID (str or int): The BookID identifying the timeline entry.
        ticketNumber (int): The new ticket number to set.

    Returns:
        tuple:
            - ("Error updating TicketNumber in Timeline for (<reportID>, <bookID>):
            <error>", "error") on failure.

    Description:
        Updates the ticket number associated with a specific ReportID and BookID in TicketTimeLine.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
                UPDATE TicketTimeLine
                SET TicketNumber = ?
                WHERE ReportID = ? AND BookID = ?;
            """,
                (ticketnumber, report_id, book_id),
            )
    except sqlite3.Error as e:
        return (
            f"Error updating TicketNumber in Timeline for ({report_id}, {book_id}): ".upper() +
            f"{e}",
            "error",
        )

    return None
