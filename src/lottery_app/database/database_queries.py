"""
DatabaseQueries module: Handles interactions with Books, ActivatedBooks, SalesLog, 
and SaleReport tables. Provides standardized database operations and error handling
for the lottery system.
"""

import sqlite3
from flask import flash

from lottery_app.database import setup_database
from lottery_app.decorators import get_db_cursor


def get_books(db):
    """
    Retrieves all book records from the Books table in the database.

    Parameters:
        db (str): Path to the SQLite database file.

    Returns:
        list: A list of dictionaries containing book information if successful.
        tuple: ("ERROR FETCHING BOOKS: <error>", "error") if an exception occurs.
    """

    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT * FROM Books ORDER BY Books.TicketPrice DESC;")
            books = cursor.fetchall()

            if not books:
                return "NO BOOKS FOUND IN DATABASE.", "error"

            books_list = []
            for book in books:
                books_list.append(
                    {
                        "BookID": book[0],
                        "GameNumber": book[1],
                        "Is_Sold": book[2],
                        "BookAmount": book[3],
                        "TicketPrice": book[4],
                        "created_at": book[5],
                        "updated_at": book[6],
                    }
                )

            return books_list
    except sqlite3.OperationalError as e:  # Database is locked, malformed, etc.
        return f"DATABASE OPERATION ERROR WHILE FETCHING BOOKS: {e}", "error"
    except sqlite3.DatabaseError as e:  # General DB errors
        return f"DATABASE ERROR WHILE FETCHING BOOKS: {e}", "error"
    except (ValueError, TypeError) as e:  # Data processing errors
        return f"DATA PROCESSING ERROR WHILE FETCHING BOOKS: {e}", "error"


def count_activated_books(db):
    """
    Counts the number of activated books in the ActivatedBooks table.

    Parameters:
        db (str): Path to the SQLite database.

    Returns:
        int: The number of activated books if successful.
        tuple: ("ERROR FETCHING ACTIVATED BOOK COUNT: <error>", "error")
        on SQLite or unexpected error.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute("SELECT COUNT(ActiveBookID)  FROM ActivatedBooks;")
            activated_book_id_count = cursor.fetchone()

            if activated_book_id_count:
                return activated_book_id_count[0]

            return "COULD NOT RETRIEVE ACTIVATED BOOKS COUNT!", "error"
    except sqlite3.Error as e:
        return f"ERROR FETCHING ACTIVATED BOOK COUNT: {e}", "error"
    except (ValueError, TypeError) as e:
        return f"UNEXPECTED ERROR WHILE COUNTING ACTIVATED BOOKS: {e}", "error"


def get_activated_books(db):
    """
    Retrieves all records from the ActivatedBooks table.

    Parameters:
        db (str): Path to the SQLite database.

    Returns:
        list: A list of dictionaries representing activated books if successful.
        tuple: ("ERROR FETCHING ACTIVATED BOOKS: <error>", "error") on SQLite or unexpected error.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute("SELECT * FROM ActivatedBooks")
            activated_books = cursor.fetchall()

            activated_books_list = []
            for book in activated_books:
                activated_books_list.append(
                    {
                        "ActivationID": book[0],
                        "ActiveBookID": book[1],
                        "isAtTicketNumber": book[3],
                        "countingTicketNumber": book[4],
                    }
                )

            return activated_books_list
    except sqlite3.Error as e:
        return f"ERROR FETCHING ACTIVATED BOOKS: {e}", "error"
    except (ValueError, TypeError) as e:
        return f"UNEXPECTED ERROR WHILE FETCHING ACTIVATED BOOKS: {e}", "error"


def is_book(db, book_id):
    """
    Checks if a book with the given BookID exists in the Books table. If a book 
    exists then all information for that book is returned.

    Parameters:
        db (str): Path to the SQLite database.
        book_id (str or int): The BookID to check.

    Returns:
        bool: True if the book exists, False otherwise.
        tuple: ("ERROR CHECKING BOOK EXISTENCE: <error>", "error") on failure.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT * FROM Books WHERE BookID = ? LIMIT 1;", (book_id,))
            book = cursor.fetchone() is not None

            if book:
                return book
            return False
    except (ValueError, TypeError) as e:
        return f"ERROR CHECKING BOOK EXISTENCE: {e}", "error"


def is_activated_book(db, activated_book_id):
    """
    Checks if a book exists in the ActivatedBooks table.

    Parameters:
        db (str): Path to the SQLite database.
        activated_book_id (str): The ActiveBookID to check.

    Returns:
        bool: True if the activated book exists, False otherwise.
        tuple: ("ERROR CHECKING ACTIVATED BOOK EXISTENCE: <error>", "error") on failure.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT * FROM ActivatedBooks WHERE ActiveBookID = ? LIMIT 1;",
                (activated_book_id,),
            )
            activated_book_id_exist = cursor.fetchone() is not None

            if activated_book_id_exist:
                return activated_book_id_exist
            return False
    except (ValueError, TypeError) as e:
        return f"ERROR CHECKING ACTIVATED BOOK EXISTENCE: {e}", "error"


def get_activated_book_is_at_ticketnumber(db, activated_book_id):
    """
    Retrieves the isAtTicketNumber(OPEN) value for a given activated book.

    Parameters:
        db (str): Path to the SQLite database.
        activated_book_id (str or int): The ActiveBookID to query.

    Returns:
        int or None: The isAtTicketNumber value if found, else None.
        tuple: ("ERROR FETCHING isAtTicketNumber: <error>", "error") on failure.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT isAtTicketNumber FROM ActivatedBooks WHERE ActiveBookID = ? LIMIT 1;",
                (activated_book_id,),
            )
            activated_book_is_at_ticketnumber = cursor.fetchone()

            return (
                activated_book_is_at_ticketnumber[0]
                if activated_book_is_at_ticketnumber
                else None
            )
    except (ValueError, TypeError) as e:
        return f"ERROR FETCHING isAtTicketNumber: {e}", "error"


def get_activated_book(db, activated_book_id):
    """
    Retrieves the full row of an activated book by ActiveBookID.

    Parameters:
        db (str): Path to the SQLite database.
        activated_book_id (str or int): The ActiveBookID to query.

    Returns:
        tuple: A tuple representing the row if found, or None if not found.
        tuple: ("ERROR FETCHING ACTIVATED BOOK: <error>", "error") on failure.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT * FROM ActivatedBooks WHERE ActiveBookID = ? LIMIT 1;",
                (activated_book_id,),
            )
            activated_book = cursor.fetchone()

            return activated_book
    except (ValueError, TypeError) as e:
        return f"ERROR FETCHING ACTIVATED BOOK: {e}", "error"


def get_book(db, book_id):
    """
    Retrieves the full row of a book from the Books table by BookID.

    Parameters:
        db (str): Path to the SQLite database.
        book_id (str or int): The BookID to query.

    Returns:
        tuple: A tuple representing the row if found, or None if not found.
        tuple: ("ERROR FETCHING BOOK: <error>", "error") on failure.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT * FROM Books WHERE BookID = ? LIMIT 1;", (book_id,))
            book = cursor.fetchone()

            return book
    except (ValueError, TypeError) as e:
        return f"ERROR FETCHING BOOK: {e}", "error"


def get_ticket_with_bookid(db, book_id):
    """
    Retrieves the first ticket timeline record associated with the given BookID.

    Parameters:
        db (str): Path to the SQLite database.
        book_id (str or int): The BookID to query.

    Returns:
        tuple: A tuple representing the timeline entry if found, or None if not found.
        tuple: ("ERROR FETCHING TICKET TIMELINE: <error>", "error") on failure.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT * FROM TicketTimeLine WHERE BookID = ? LIMIT 1;", (book_id,))
            ticket = cursor.fetchone()

            return ticket
    except (ValueError, TypeError) as e:
        return f"ERROR FETCHING TICKET TIMELINE: {e}", "error"


def get_all_active_book_ids(db):
    """
    Retrieves all active book IDs from the ActivatedBooks table.

    Parameters:
        db (str): Path to the SQLite database.

    Returns:
        list: A list of ActiveBookID values if successful (can be empty if none exist).
        tuple: ("ERROR FETCHING ACTIVE BOOK IDS: <error>", "error") if a database error occurs.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute("SELECT ActiveBookID FROM ActivatedBooks")
            # Fetch all results
            active_book_ids = cursor.fetchall()
            # Optionally, flatten the result if you just want a list of IDs
            active_book_ids = [row[0] for row in active_book_ids]

            return active_book_ids
    except sqlite3.Error as e:
        return f"ERROR FETCHING ACTIVE BOOK IDS: {e}", "error"
    except (ValueError, TypeError) as e:
        return f"UNEXPECTED ERROR WHILE FETCHING ACTIVE BOOK IDS: {e}", "error"


def get_scan_ticket_page_table(db):
    """
    Returns a list of active books along with their ticket info, sorted by ticket price (desc).
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            cursor.execute(
                """
                SELECT TicketNameLookup.TicketName, ActivatedBooks.ActiveBookID, Books.TicketPrice,
                Books.GameNumber, Books.Is_Sold, ActivatedBooks.isAtTicketNumber, 
                ActivatedBooks.countingTicketNumber
                FROM ActivatedBooks
                Join Books ON ActiveBookID = BookID
                Left Join TicketNameLookup ON Books.GameNumber = TicketNameLookup.GameNumber
                ORDER BY Books.TicketPrice DESC;
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "TicketName": row[0],
                    "ActiveBookID": row[1],
                    "ticketPrice": row[2],
                    "GameNumber": row[3],
                    "Is_Sold": row[4],
                    "isAtTicketNumber": row[5],
                    "countingTicketNumber": row[6],
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_scan_ticket_page_table: {e}", "error"


def is_counting_ticket_number_set(db, activated_book_id):
    """
    Checks if the countingTicketNumber is set for a given activated book.

    Parameters:
        db (str): Path to the SQLite database.
        activated_book_id (str or int): The ActiveBookID to check.

    Returns:
        bool: True if countingTicketNumber is set, False if not set or book doesn't exist.
        tuple: ("ERROR CHECKING countingTicketNumber: <error>", "error") on failure.
    """
    try:
        setup_database.initialize_database(db)
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT countingTicketNumber FROM ActivatedBooks WHERE ActiveBookID = ? LIMIT 1;",
                (activated_book_id,),
            )
            result = cursor.fetchone()

            if result and result[0] is not None:
                return True
            return False
    except (ValueError, TypeError) as e:
        return f"ERROR CHECKING countingTicketNumber: {e}", "error"


def get_all_instant_tickets_sold_quantity(db, report_id):
    """
    Returns all ticket sales for a specific report.
    """

    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT SalesLog.ActiveBookID, SalesLog.Ticket_Sold_Quantity, Books.TicketPrice
                FROM SalesLog
                JOIN Books ON ActiveBookID = BookID
                WHERE SalesLog.ReportID = ?;
            """
            cursor.execute(query, (report_id,))
            rows = cursor.fetchall()
            return [
                {
                    "ActiveBookID": row[0],
                    "Ticket_Sold_Quantity": row[1],
                    "TicketPrice": row[2],
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_all_instant_tickets_sold_quantity: {e}", "error"


def get_all_sold_books(db, report_id):
    """
    Returns only books marked as sold for a specific report.
    """

    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT ActiveBookID, Ticket_Sold_Quantity, Books.TicketPrice
                FROM SalesLog
                JOIN Books ON ActiveBookID = BookID
                WHERE ReportID = ? and Is_Sold = True;
            """
            cursor.execute(query, (report_id,))
            rows = cursor.fetchall()
            return [{"BookID": row[0]} for row in rows]
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_all_sold_books: {e}", "error"


def is_sold(db, book_id):
    """
    Returns True or False if the book is sold. Returns error on failure.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT Is_Sold
                FROM Books
                WHERE BookID = ?;
            """
            cursor.execute(query, (book_id,))
            result_table = cursor.fetchone()
            return result_table[0]
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN FETCHING is_sold: {e}", "error"


def get_table_for_invoice(db, report_id):
    """
    Returns ticket details needed for invoice generation for a report.
    """

    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT SalesLog.Ticket_Name, SalesLog.Ticket_GameNumber, SalesLog.ActiveBookID,
                Books.TicketPrice, SalesLog.prev_TicketNum, SalesLog.current_TicketNum,
                SalesLog.Ticket_Sold_Quantity
                FROM SalesLog
                Join Books ON ActiveBookID = BookID
                Where ReportID = ?
                ORDER BY Books.TicketPrice DESC;
            """
            cursor.execute(query, (report_id,))
            rows = cursor.fetchall()
            return [
                {
                    "TicketName": row[0],
                    "Ticket_GameNumber": row[1],
                    "ActiveBookID": row[2],
                    "TicketPrice": row[3],
                    "Open": row[4],
                    "Close": row[5],
                    "Sold": row[6],
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_table_for_invoice: {e}", "error"


def get_daily_report(db, report_id):
    """
    Returns the full sale report (aka session report) by ReportID.
    """

    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT *
                FROM SaleReport
                Where ReportID = ?;
            """
            cursor.execute(query, (report_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "ReportID": row[0],
                    "ReportDate": row[1],
                    "ReportTime": row[2],
                    "InstantTicketSold": row[3],
                    "OnlineTicketSold": row[4],
                    "InstantTicketCashed": row[5],
                    "OnlineTicketCashed": row[6],
                    "CashOnHand": row[7],
                    "TotalDue": row[8],
                }
            return f"NO DAILY REPORT FOUND FOR ReportID({report_id})", "error"
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_daily_report: {e}", "error"


def get_all_sales_reports(db):
    """
    Returns all sale reports sorted by ReportID descending.
    """
    setup_database.initialize_database(db)
    # Not really daily report but a session report
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT *
                FROM SaleReport
                ORDER BY CAST(ReportID AS INTEGER) DESC;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                {
                    "ReportID": row[0],
                    "ReportDate": row[1],
                    "ReportTime": row[2],
                    "InstantTicketSold": row[3],
                    "OnlineTicketSold": row[4],
                    "InstantTicketCashed": row[5],
                    "OnlineTicketCashed": row[6],
                    "CashOnHand": row[7],
                    "TotalDue": row[8],
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        raise RuntimeError(f"DATABASE ERROR IN get_all_sales_reports: {e}") from e


def get_sales_log(db, report_id):
    """
    Returns a list of all ticket sales for the given ReportID.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT *
                FROM SalesLog
                Where ReportID = ?;
            """
            cursor.execute(query, (report_id,))
            rows = cursor.fetchall()
            return [
                {
                    "ActiveBookID": row[3],
                    "Open": row[4],
                    "Close": row[5],
                    "Sold": row[6],
                    "Game Name": row[7],
                    "Game #": row[8],
                }
                for row in rows
            ]
    except sqlite3.Error as e:
        return f"Database ERROR IN get_sales_log: {e}", "error"


def get_sales_log_with_bookid(db, report_id, book_id):
    """
    Returns the sales log entry for a given ReportID and book_id.
    """

    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT *
                FROM SalesLog
                Where ReportID = ? and ActiveBookID = ?;
            """
            cursor.execute(query, (report_id, book_id))
            row = cursor.fetchone()
            if row:
                return {
                    "ActiveBookID": row[3],
                    "Open": row[4],
                    "Close": row[5],
                    "Sold": row[6],
                    "Game Name": row[7],
                    "Game #": row[8],
                }
            return (
                f"No entry found for ReportID {report_id} and BookID {book_id}".upper(),
                "error",
            )
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_sales_log_with_bookid: {e}", "error"


def get_gm_from_lookup(db):
    """
    Returns a set of all game numbers in the TicketNameLookup table.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT GameNumber
                FROM TicketNameLookup;
            """
            cursor.execute(query)
            return set(row[0] for row in cursor.fetchall())
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_gm_from_lookup: {e}", "error"


def get_ticket_name(db, game_number):
    """
    Returns the ticket name for the given game number.
    Returns 'N/A' if not found.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            query = """
                SELECT TicketName
                FROM TicketNameLookup
                Where GameNumber = ?;
            """
            cursor.execute(query, (game_number,))
            result = cursor.fetchone()
            return result[0] if result else "N/A"
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_ticket_name: {e}", "error"


def next_report_id(db):
    """
    Returns the next ReportID (as a string). Starts from '1' if no reports exist.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT ReportID FROM SaleReport ORDER BY CAST(ReportID AS INTEGER) DESC LIMIT 1"
            )
            row = cursor.fetchone()
            print(row)
            return str(int(row[0]) + 1) if row else "1"
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN next_report_ID: {e}", "error"


def get_game_num_of(db, book_id):
    """
    Returns the GameNumber for a given BookID.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            cursor.execute(
                "SELECT GameNumber FROM Books Where BookID = ? LIMIT 1", (book_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_game_num_of: {e}", "error"


def can_submit(db):
    """
    Returns True if all activated books have a countingTicketNumber set.
    Returns False if any are missing.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            cursor.execute("SELECT countingTicketNumber FROM ActivatedBooks")
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    if row[0] is None:
                        return False
                return True
            return True
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN can_Submit: {e}", "error"


def was_activated(db, book_id):
    """
    Returns the latest TicketNumber from the TicketTimeline table for a given BookID.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            cursor.execute(
                """SELECT TicketNumber FROM TicketTimeLine where BookID = ? 
                ORDER BY CAST(ReportID AS INTEGER) DESC""",
                (book_id,),
            )
            rows = cursor.fetchall()

            if rows:
                return rows[0][0]
            return None
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN was_activated: {e}", "error"


def get_all_users(db):
    """
    Return all the usersnames and roles from the database.
    """
    setup_database.initialize_database(db)
    try:
        with get_db_cursor(db) as cursor:
            cursor.execute("SELECT username, role FROM users")
            users = cursor.fetchall()
            # Convert to list of dictionaries (Flask/Jinja-friendly)
            return [{"username": u[0], "role": u[1]} for u in users]
    except sqlite3.Error as e:
        return f"DATABASE ERROR IN get_all_users: {e}", "error"
