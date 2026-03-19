"""
Database management module for the Books table in lottery database system.
"""

import datetime
import sqlite3

from lottery_app.database.setup_database import initialize_database
from lottery_app.decorators import get_db_cursor


def add_book(cursor, book_info):
    """
    Inserts a book record into the database.

    Parameters:
        book_info (dict): A dictionary with keys:
            - BookID
            - GameNumber
            - BookAmount
            - isAtTicketNumber
            - TicketPrice
    """
    cursor.execute(
        """
        INSERT INTO Books (BookID, GameNumber, Is_Sold, BookAmount, TicketPrice)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            book_info["BookID"],
            book_info["GameNumber"],
            book_info["Is_Sold"],
            book_info["BookAmount"],
            book_info["TicketPrice"],
        ),
    )


def insert_book_info_to_books_table(database_path, book_info):
    """
    Inserts a book record into the 'Books' table of the specified SQLite database.

    Parameters:
        database_path (str): The path to the SQLite database file.
        book_info (dict): The book data to be inserted. The format must match
                            the expected input of the add_book() function.

    Returns:
        tuple: A tuple containing a status message and a status type:
               - ("BOOK ADDED!", "success") if insertion was successful.
               - ("BOOK IS ALREADY IN THE DATABASE", "error") if the BookID already exists.
               - ("BOOK INSERTION ERROR: <error>", "error") for any other database error.
    """

    initialize_database(database_path)
    try:
        with get_db_cursor(database_path) as cursor:
            add_book(cursor, book_info)
    except sqlite3.Error as e:
        if "UNIQUE constraint failed: Books.BookID" in str(e):
            return "BOOK IS ALREADY IN THE DATABASE", "error"
        return f"BOOK INSERTION ERROR: {e}", "error"

    return "SUCCESSFULLY UPDATED BOOKS TABLE", "success"


def book_is_sold(
    cursor,
    is_sold,
    book_id,
    date=datetime.datetime.now(datetime.timezone.utc).time().strftime("%H:%M:%S"),
):
    """
    Updates the 'Is_Sold' status of a book in the Books table.

    Parameters:
        cursor (sqlite3.Cursor): The database cursor to execute SQL.
        conn (sqlite3.Connection): The open connection to the database.
        is_sold (int): The new value to set for the Is_Sold column (e.g., 0 or 1).
        book_id (str): The ID of the book to update.
        date: The timestamp to set as 'updated_at'. Defaults to current UTC time.

    Description:
        This function updates the 'Is_Sold' flag and the 'updated_at' timestamp
        for the specified book in the database.
    """
    cursor.execute(
        """
        UPDATE Books
        SET Is_Sold = ?,
        updated_at = ?
        WHERE BookID = ?
    """,
        (is_sold, date, book_id),
    )


def update_is_sold_for_book(database_path, is_sold, book_id):
    """
    Updates the 'Is_Sold' status for a specific book in the database.

    Parameters:
        database_path (str): The path to the SQLite database file.
        is_sold (bool or int): The new sold status to set (e.g., 0 or 1).
        book_id (str or int): The ID of the book to update.

    Returns:
        tuple:
            - ("BOOK SOLD STATUS UPDATED", "success") on success.
            - ("ERROR UPDATING SOLD VALUE TO <is_sold>: <error>", "error") on failure.

    Description:
        This function:
        1. Delegates the actual update to the `book_is_sold` helper function.
        2. Catches and returns any SQLite errors.
    """
    initialize_database(database_path)
    try:
        with get_db_cursor(database_path) as cursor:
            book_is_sold(cursor, is_sold, book_id)
    except sqlite3.Error as e:
        return f"ERROR UPDATING SOLD VALUE TO {is_sold}: {e}", "error"

    return "SUCCESSFULLY UPDATED BOOKS TABLE", "success"


def delete_book(database_path, book_id):
    """
    Deletes a book entry from the Books table by its BookID.

    Parameters:
        database_path (str): Path to the SQLite database.
        book_id (str or int): The BookID to delete.

    Returns:
        tuple:
            - ("Book deletion error for bookID(<book_id>): <error>", "error") on failure.

    Description:
        Removes a book record permanently from the Books table.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
                DELETE FROM Books Where BookID = ?;
            """,
                (book_id,),
            )
    except sqlite3.Error as e:
        return f"Book deletion error for bookID({book_id}): ".upper() + f"{e}", "error"

    return "SUCCESSFULLY UPDATED BOOKS TABLE", "success"
