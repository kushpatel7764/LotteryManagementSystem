"""
Database management module for the Sales Log table in lottery database system.
"""

import sqlite3

from src.database.setup_database import initialize_database
from src.decorators import get_db_cursor
from src.utils.config import load_config


def add_sales_log(cursor, scanned_ticket_info):
    """
    ActiveBookID VARCHAR(255),
    prev_TicketNum INTEGER,
    current_TicketNum INTEGER,
    Ticket_Sold_Quantity INTEGER, (Calculated)
    Ticket_Name TEXT,
    Ticket_GameNumber VARCHAR(255),
    ReportID is PENDING
    """
    counting_order = load_config()["ticket_order"]
    if counting_order == "descending":
        sold = int(scanned_ticket_info["prev_TicketNum"]) - int(
            scanned_ticket_info["current_TicketNum"]
        )
    else:
        sold = int(scanned_ticket_info["current_TicketNum"]) - int(
            scanned_ticket_info["prev_TicketNum"]
        )
    cursor.execute(
        """
        INSERT INTO SalesLog (ActiveBookID, prev_TicketNum, current_TicketNum, 
        Ticket_Sold_Quantity, Ticket_Name, Ticket_GameNumber)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            scanned_ticket_info["ActiveBookID"],
            scanned_ticket_info["prev_TicketNum"],
            scanned_ticket_info["current_TicketNum"],
            sold,
            scanned_ticket_info["Ticket_Name"],
            scanned_ticket_info["Ticket_GameNumber"],
        ),
    )


def add_sales_log_at_report_id(cursor, scanned_ticket_info):
    """
    ActiveBookID VARCHAR(255),
    prev_TicketNum INTEGER,
    current_TicketNum INTEGER,
    Ticket_Sold_Quantity INTEGER, (Calculated)
    Ticket_Name TEXT,
    Ticket_GameNumber VARCHAR(255),
    REPPORT is specified reportID
    """
    counting_order = load_config()["ticket_order"]
    if counting_order == "descending":
        sold = int(scanned_ticket_info["prev_TicketNum"]) - int(
            scanned_ticket_info["current_TicketNum"]
        )
    else:
        sold = int(scanned_ticket_info["current_TicketNum"]) - int(
            scanned_ticket_info["prev_TicketNum"]
        )
    cursor.execute(
        """
        INSERT INTO SalesLog (ReportID ,ActiveBookID, prev_TicketNum, current_TicketNum,
        Ticket_Sold_Quantity, Ticket_Name, Ticket_GameNumber)
        VALUES (? ,?, ?, ?, ?, ?, ?)
        """,
        (
            scanned_ticket_info["ReportID"],
            scanned_ticket_info["ActiveBookID"],
            scanned_ticket_info["prev_TicketNum"],
            scanned_ticket_info["current_TicketNum"],
            sold,
            scanned_ticket_info["Ticket_Name"],
            scanned_ticket_info["Ticket_GameNumber"],
        ),
    )


def insert_sales_log(database_path, scanned_ticket_info):
    """
    Inserts a sales log entry into the SalesLog table based on scanned ticket data.

    Parameters:
        database_path (str): The file path to the SQLite database.
        scanned_ticket_info (dict): Dictionary containing ticket information.
                                    If it includes "ReportID", logs the sale under that report.
                                    Otherwise, it logs the sale with a default/pending status.

    Returns:
        tuple:
            - ("ERROR LOGGING TICKET SALE DATA: <error>", "error") on SQLite error.
    """
    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            if "ReportID" in scanned_ticket_info:
                add_sales_log_at_report_id(cursor, scanned_ticket_info)
            else:
                add_sales_log(cursor, scanned_ticket_info)
            return (
                f"TICKET({scanned_ticket_info['ActiveBookID']}) SALE HAS BEEN LOGGED",
                "success",
            )
    except sqlite3.Error as e:
        return f"ERROR LOGGING TICKET SALE DATA: {e}", "error"


def delete_sales_log_by_book_id(database_path, book_id):
    """
    Deletes all pending sales log entries for a specific book from the SalesLog table.

    Parameters:
        database_path (str): The file path to the SQLite database.
        book_id (str or int): The ActiveBookID whose pending sales logs should be deleted.

    Returns:
        tuple:
            - ("Sales log entries deleted for BookID (<book_id>)", 
            "success") on successful deletion.
            - ("ERROR DELETING LOGGED SALE DATA FOR BOOKID(<book_id>): 
            <error>", "error") on SQLite error.

    Description:
        This function deletes records from the SalesLog table where ActiveBookID
        matches the given book_id and ReportID is 'Pending'. This is used to
        clear temporary log entries.
    """
    # Deletes only current Sales log

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                "DELETE FROM SalesLog WHERE ActiveBookID = ? AND ReportID = 'Pending';",
                (book_id,),
            )
    except sqlite3.Error as e:
        return f"ERROR DELETING LOGGED SALE DATA FOR BOOKID({book_id}): {e}", "error"

    return "SUCCESSFULLY UPDATED SALES LOG TABLE", "success"


def update_pending_sales_log_report_id(database_path, report_id):
    """
    Updates all 'Pending' sales log entries by assigning them a specified ReportID.

    Parameters:
        database_path (str): The path to the SQLite database file.
        report_id (str or int): The ReportID to assign to all sales log entries currently
        marked as 'Pending'.

    Returns:
        tuple:
            - ("ERROR SETTING REPORTID FOR PENDING SALE LOG: <error>", "error") on failure.

    Description:
        This function connects to the database and updates all entries in the SalesLog table
        with a ReportID of 'Pending', setting them to the specified report_id.
        Useful when finalizing a batch of scanned ticket sales into a report.
    """
    initialize_database(database_path)
    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
            UPDATE SalesLog
            SET ReportID = ?
            WHERE ReportID = 'Pending';
            """,
                (report_id,),
            )
    except sqlite3.Error as e:
        return f"ERROR SETTING REPORTID FOR PENDING SALE LOG: {e}", "error"

    return "SUCCESSFULLY UPDATED SALES LOG TABLE", "success"


def update_sales_log_prev_ticketnum(
    database_path, prev_ticketnum, report_id, active_book_id
):
    """
    Updates the `prev_TicketNum` in the SalesLog table and recalculates the quantity sold.

    Parameters:
        database_path (str): Path to the SQLite database.
        prev_TicketNum (int): The previous (starting) ticket number.
        report_id (str or int): The ReportID of the sale.
        ActiveBookID (str or int): The ActiveBookID associated with the sale.

    Returns:
        tuple:
            - ("NO MATCHING SALE ENTRY FOUND.", "error") if no record is found.
            - ("ERROR UPDATING OPEN VALUE FOR LOGGED SALES: <error>", "error") on SQLite error.
            - None if the update is successful.

    Description:
        This function:
        1. Retrieves the current_TicketNum for the specified report/book.
        2. Calculates the number of tickets sold based on the counting order from config.
        3. Updates both `prev_TicketNum` and `Ticket_Sold_Quantity` in the SalesLog table.
    """
    # Also updates the qunatity sold
    initialize_database(database_path)
    try:
        with get_db_cursor(database_path) as cursor:
            # Step 1: Get current_TicketNum from the DB
            cursor.execute(
                """
                SELECT current_TicketNum FROM SalesLog
                WHERE ReportID = ? AND ActiveBookID = ?;
            """,
                (report_id, active_book_id),
            )

            row = cursor.fetchone()
            if row is None:
                return "OPENING REPORT NOT UPDATED AS IT IS NOT NECESSARY", "warning"

            current_ticketnum = int(row[0])
            counting_order = load_config()["ticket_order"]
            if counting_order == "descending":
                sold = int(prev_ticketnum) - int(current_ticketnum)
            else:
                sold = int(current_ticketnum) - int(prev_ticketnum)

            cursor.execute(
                """
            UPDATE SalesLog
            SET prev_TicketNum = ?, Ticket_Sold_Quantity = ?
            WHERE ReportID = ? AND ActiveBookID = ?;
            """,
                (prev_ticketnum, sold, report_id, active_book_id),
            )
    except sqlite3.Error as e:
        return f"ERROR UPDATING OPEN VALUE FOR LOGGED SALES: {e}", "error"

    return "SUCCESSFULLY UPDATED SALES LOG TABLE", "success"


def update_sales_log_current_ticketnum(
    database_path, current_ticketnum, report_id, active_book_id
):
    """
    Updates the `current_TicketNum` in the SalesLog table and recalculates the quantity sold.

    Parameters:
        database_path (str): Path to the SQLite database.
        current_TicketNum (int): The current (ending) ticket number.
        report_id (str or int): The ReportID of the sale.
        ActiveBookID (str or int): The ActiveBookID associated with the sale.

    Returns:
        tuple:
            - ("NO MATCHING SALE ENTRY FOUND.", "error") if no record is found.
            - ("ERROR UPDATING OPEN VALUE FOR LOGGED SALES: <error>", "error") on SQLite error.
            - None if the update is successful.

    Description:
        This function:
        1. Retrieves the `prev_TicketNum` from the database.
        2. Calculates the quantity of tickets sold using the config's ticket counting order.
        3. Updates `current_TicketNum` and `Ticket_Sold_Quantity` accordingly.
    """

    # Also updates the qunatity sold
    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            # Step 1: Get current_TicketNum from the DB
            cursor.execute(
                """
                SELECT prev_TicketNum FROM SalesLog
                WHERE ReportID = ? AND ActiveBookID = ?;
            """,
                (report_id, active_book_id),
            )

            row = cursor.fetchone()
            if row is None:
                return "CLOSING REPORT NOT UPDATED AS IT IS NOT NECESSARY", "warning"

            prev_ticketnum = int(row[0])
            counting_order = load_config()["ticket_order"]
            if counting_order == "descending":
                sold = int(prev_ticketnum) - int(current_ticketnum)
            else:
                sold = int(current_ticketnum) - int(prev_ticketnum)

            cursor.execute(
                """
            UPDATE SalesLog
            SET current_TicketNum = ?, Ticket_Sold_Quantity = ?
            WHERE ReportID = ? AND ActiveBookID = ?;
            """,
                (current_ticketnum, sold, report_id, active_book_id),
            )
    except sqlite3.Error as e:
        return f"ERROR UPDATING OPEN VALUE FOR LOGGED SALES: {e}", "error"

    return "SUCCESSFULLY UPDATED SALES LOG TABLE", "success"
