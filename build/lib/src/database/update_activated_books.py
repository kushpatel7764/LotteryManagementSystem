"""
Database management module for the Activated Books table in lottery database system.
"""


import datetime
import sqlite3

from src.database.setup_database import initialize_database
from src.decorators import get_db_cursor


def add_activate_book_info_to_activated_book(cursor, activated_book_info):
    """
    Inserts a book into the ActivatedBooks table.

    Parameters:
        activated_book_info (dict): A dictionary with keys:
            - ActivationID
            - ActiveBookID
            - Is_Sold
            - isAtTicketNumber
    """
    cursor.execute(
        """
        INSERT INTO ActivatedBooks (ActivationID, ActiveBookID, isAtTicketNumber)
        VALUES (?, ?, ?)
    """,
        (
            activated_book_info["ActivationID"],
            activated_book_info["ActiveBookID"],
            activated_book_info["isAtTicketNumber"],
        ),
    )


def insert_book_to_activated_book_table(database_path, active_book_info):
    """
    Inserts an activated book record into the 'ActivatedBook' table of the specified 
    SQLite database.

    Parameters:
        database_path (str): The file path to the SQLite database.
        active_book_info (dict): A dictionary containing information about the activated
        book. 

    Returns:
        tuple: a message and status type.

    Description:
        1. Attempts to insert the activation info using
        `add_activate_book_info_to_Activated_Book`.
        2. Returns an error message on failure or None on success.
    """
    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            add_activate_book_info_to_activated_book(cursor, active_book_info)
    except sqlite3.Error as e:
        return f"ERROR ACTIVATING BOOK: {e}", "error"

    return "SUCCESSFULLY UPDATED ACTIVATED BOOK TABLE", "success"


def update_counting_ticket_number_for_book_id_query(
    cursor, book_id, new_ticket_number, date=datetime.datetime.now(
        datetime.timezone.utc).time().strftime("%H:%M:%S"), ):
    """
    Query to update the counting ticket number to a new number for a given book in the
    ActivatedBooks table.
    """
    # SQL query to update the countingTicketNumber
    update_query = """
    UPDATE ActivatedBooks
    SET countingTicketNumber = ?,
    updated_at = ?
    WHERE ActiveBookID = ? AND countingTicketNumber is NULL;
    """
    # Execute the update query
    cursor.execute(update_query, (new_ticket_number, date, book_id))


def update_counting_ticket_number(database_path, book_id, new_ticket_number):
    """
    Updates the counting ticket number to a new number for a given book in the
    ActivatedBooks table.

    Parameters:
        database_path (str): The path to the SQLite database file.
        book_id (str): The unique identifier of the book whose ticket number is
        being updated. new_ticket_number (int): The new ticket number to set 
        for the book.

    Returns:
        tuple: A tuple containing:
               - A success message and status 
               ("COUNTING TICKET NUMBER UPDATED!", "success") if successful.
               - An error message and status 
               ("ERROR UPDATING CLOSE VALUE: <error>", "error") if an 
               SQLite error occurs.

    Description:
        This function:
        1. Attempts to update the ticket number associated with the provided book ID
           by calling `update_counting_ticket_number_for_book_id_query`.
        2. Catches and returns any SQLite errors encountered.
    """
    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            update_counting_ticket_number_for_book_id_query(
                cursor, book_id, new_ticket_number
            )
    except sqlite3.Error as e:
        return f"ERROR UPDATING CLOSE VALUE: {e}", "error"

    return "SUCCESSFULLY UPDATED ACTIVATED BOOK TABLE", "success"


def deactivate_book(database_path, book_id):
    """
    Removes the activation record of a book from the ActivatedBooks table.

    Parameters:
        database_path (str): Path to the SQLite database.
        book_id (str or int): The ActiveBookID to deactivate (delete).

    Returns:
        tuple:
            - ("Error deactivating book: <error>", "error") on failure.
            - None on success.

    Description:
        Deletes the row corresponding to the given ActiveBookID from ActivatedBooks.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                "DELETE FROM ActivatedBooks WHERE ActiveBookID = ?;", (book_id,))
    except sqlite3.Error as e:
        return "Error deactivating book: ".upper() + f"{e}", "error"

    return "SUCCESSFULLY UPDATED ACTIVATED BOOK TABLE", "success"


def update_is_at_ticketnumbers(database_path):
    """
    Sets the 'isAtTicketNumber' field to the value of 'countingTicketNumber' for 
    all activated books.

    Parameters:
        database_path (str): Path to the SQLite database.

    Returns:
        tuple:
            - ("An error occurred while setting new open values for activated books:
            <error>", "error") on failure.

    Description:
        This function updates every row in ActivatedBooks so that isAtTicketNumber
        matches countingTicketNumber.
    """
    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute("""
                UPDATE ActivatedBooks
                SET isAtTicketNumber = countingTicketNumber
            """)
    except sqlite3.Error as e:
        return (
            "An error occured while setting new open values for activated books: ".upper() +
            f"{e}",
            "error",
        )

    return "SUCCESSFULLY UPDATED ACTIVATED BOOK TABLE", "success"


def update_is_at_ticketnumber_val(database_path, book_id, new_val):
    """
    Updates the 'isAtTicketNumber' field for a single activated book to a new value.

    Parameters:
        database_path (str): Path to the SQLite database.
        bookID (str or int): The ActiveBookID to update.
        newVal (int): New value for isAtTicketNumber.

    Returns:
        tuple:
            - ("Error updating open value to <newVal> at bookID(<bookID>):
            <error>", "error") on failure.

    Description:
        Updates isAtTicketNumber for the specified book with the given value.
    """

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
                UPDATE ActivatedBooks
                SET isAtTicketNumber = ?
                WHERE ActiveBookID = ?
            """,
                (new_val, book_id),
            )
    except sqlite3.Error as e:
        return (
            f"Error updating open value to {new_val} at bookID({book_id}): ".upper() +
            f"{e}",
            "error",
        )

    return "SUCCESSFULLY UPDATED ACTIVATED BOOK TABLE", "success"


def clear_counting_ticket_numbers(database_path):
    """
    Clears the 'countingTicketNumber' field (sets to NULL) for all activated books records.

    Parameters:
        database_path (str): Path to the SQLite database.

    Returns:
        tuple:
            - ("An error occurred while clearing old closing values:
            <error>", "error") on failure.

    Description:
        Resets countingTicketNumber to NULL in all rows of ActivatedBooks.
    """

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute("""
                UPDATE ActivatedBooks
                SET countingTicketNumber = NULL
            """)
    except sqlite3.Error as e:
        return (
            "An Error occured while clearing old closing values: ".upper() +
            f"{e}",
            "error",
        )

    return "SUCCESSFULLY UPDATED ACTIVATED BOOK TABLE", "success"


def clear_counting_ticket_number(database_path, book_id):
    """
    Clears the 'countingTicketNumber' field (sets to NULL) for a single activated book.

    Parameters:
        database_path (str): Path to the SQLite database.
        book_id (str): The ActiveBookID whose countingTicketNumber should be cleared.

    Returns:
        tuple:
            - ("Unable to clear closing value at bookID(<book_id>):
            <error>", "error") on failure.

    Description:
        Resets countingTicketNumber to NULL for the specified book.
    """

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                "UPDATE ActivatedBooks SET countingTicketNumber = NULL WHERE ActiveBookID = ?",
                (book_id,),
            )
    except sqlite3.Error as e:
        return (
            f"Unable to clear closing value at bookID({book_id})".upper() +
            f"{e}",
            "error",
        )

    return "SUCCESSFULLY UPDATED ACTIVATED BOOK TABLE", "success"
