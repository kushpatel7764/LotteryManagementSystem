import os
import sqlite3
import datetime
from utils.config import load_config
from decorators import get_db_cursor


# Connect to database
def setup_database_schema_with_sql_file(cursor, sql_filename):
    """
    Executes an SQL schema script to set up or modify the structure of a SQLite database.

    Parameters:
        cursor (sqlite3.Cursor): The cursor object used to execute SQL commands.
        sql_filename (str): The filename of the SQL file containing the schema setup instructions.

    Description:
        This function locates the provided SQL file (assumed to be one directory above the script),
        reads its contents, and executes the SQL script using the given database cursor.
        After execution, it commits the changes to the database.
    """
    try:
        setup_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sql_file_path = os.path.join(setup_dir, sql_filename)

        # Read the SQL schema file
        with open(sql_file_path, "r") as file:
            sql_script = file.read()

        cursor.executescript(sql_script)
    except Exception as e:
        print(f"Error setting up database schema: {e}")
        raise


def initialize_database(database_path):
    """
    Initializes a new or existing SQLite database by setting up its schema.

    Parameters:
        database_path (str): The file path to the SQLite database file.
    """

    with get_db_cursor(database_path) as cursor:
        setup_database_schema_with_sql_file(cursor, "Lottery_DB_Schema.sql")


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


def insert_book_info_to_Books_table(database_path, book_info):
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
    return "BOOK ADDED!", "success"


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


def add_ticket_to_timeline_at_reportID(cursor, ticket_info):
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


def insert_ticket_to_TicketTimeline_table(database_path, ticket_info):
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
                add_ticket_to_timeline_at_reportID(cursor, ticket_info)
            else:
                add_ticket_to_timeline(cursor, ticket_info)
    except sqlite3.IntegrityError as e:
        return f"INTEGRITY ERROR SETTING TICKET TIMELINE: {e}", "error"
    except sqlite3.Error as e:
        return f"ERROR INSERTING SETTING TICKET TIMELINE: {e}", "error"

    return "TICKET SUCCESSFULLY INSERTED!", "success"


def add_activate_book_info_to_Activated_Book(cursor, activated_book_info):
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


def insert_book_to_ActivatedBook_table(database_path, active_book_info):
    """
    Inserts an activated book record into the 'ActivatedBook' table of the specified SQLite database.

    Parameters:
        database_path (str): The file path to the SQLite database.
        active_book_info (dict): A dictionary containing information about the activated book.
                                 Must include the key "ActiveBookID" for success message formatting.

    Returns:
        tuple: a message and status type.

    Description:
        1. Attempts to insert the activation info using `add_activate_book_info_to_Activated_Book`.
        2. Returns an error message on failure, or a success message including the ActiveBookID.
    """
    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            add_activate_book_info_to_Activated_Book(cursor, active_book_info)
    except sqlite3.Error as e:
        return f"ERROR ACTIVATING BOOK: {e}", "error"

    return f"Book ({active_book_info['ActiveBookID']}) has been activated!", "success"


def update_counting_ticket_number_for_book_id_query(
    cursor,
    book_id,
    new_ticket_number,
    date=datetime.datetime.now(datetime.timezone.utc).time().strftime("%H:%M:%S"),
):
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
    Updates the counting ticket number to a new number for a given book in the ActivatedBooks table.

    Parameters:
        database_path (str): The path to the SQLite database file.
        book_id (str): The unique identifier of the book whose ticket number is being updated.
        new_ticket_number (int): The new ticket number to set for the book.

    Returns:
        tuple: A tuple containing:
               - A success message and status ("COUNTING TICKET NUMBER UPDATED!", "success") if successful.
               - An error message and status ("ERROR UPDATING CLOSE VALUE: <error>", "error") if an SQLite error occurs.

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


def delete_TicketTimeLine_by_book_id(database_path, book_id):
    """
    Deletes ticket entries for a specific book from the TicketTimeLine table
    where the ReportID is marked as 'Pending'.

    Parameters:
        database_path (str): The file path to the SQLite database.
        book_id (str or int): The BookID whose associated pending timeline entries should be deleted.

    Returns:
        tuple:
            - ("ERROR DELETING TICKETTIMELINE BOOKID(<book_id>): <error>", "error") on failure.
    """

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                "DELETE FROM TicketTimeLine WHERE BookID = ? AND ReportID = 'Pending';",
                (book_id,),
            )
    except sqlite3.Error as e:
        return f"ERROR DELETING TICKETTIMELINE BOOKID({book_id}): {e}", "error"


def book_is_sold(
    cursor,
    isSold,
    book_id,
    date=datetime.datetime.now(datetime.timezone.utc).time().strftime("%H:%M:%S"),
):
    """
    Updates the 'Is_Sold' status of a book in the Books table.

    Parameters:
        cursor (sqlite3.Cursor): The database cursor to execute SQL.
        conn (sqlite3.Connection): The open connection to the database.
        isSold (int): The new value to set for the Is_Sold column (e.g., 0 or 1).
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
        (isSold, date, book_id),
    )


def update_is_sold_for_book(database_path, isSold, book_id):
    """
    Updates the 'Is_Sold' status for a specific book in the database.

    Parameters:
        database_path (str): The path to the SQLite database file.
        isSold (bool or int): The new sold status to set (e.g., 0 or 1).
        book_id (str or int): The ID of the book to update.

    Returns:
        tuple:
            - ("BOOK SOLD STATUS UPDATED", "success") on success.
            - ("ERROR UPDATING SOLD VALUE TO <isSold>: <error>", "error") on failure.

    Description:
        This function:
        1. Delegates the actual update to the `book_is_sold` helper function.
        2. Catches and returns any SQLite errors.
    """
    initialize_database(database_path)
    try:
        with get_db_cursor(database_path) as cursor:
            book_is_sold(cursor, isSold, book_id)
    except sqlite3.Error as e:
        return f"ERROR UPDATING SOLD VALUE TO {isSold}: {e}", "error"


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
                   INSERT INTO SalesLog (ActiveBookID, prev_TicketNum, current_TicketNum, Ticket_Sold_Quantity, Ticket_Name, Ticket_GameNumber)
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
                   INSERT INTO SalesLog (ReportID ,ActiveBookID, prev_TicketNum, current_TicketNum, Ticket_Sold_Quantity, Ticket_Name, Ticket_GameNumber)
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
            return f"TICKET({scanned_ticket_info["ActiveBookID"]}) SALE HAS BEEN LOGGED", "success"
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
            - ("Sales log entries deleted for BookID (<book_id>)", "success") on successful deletion.
            - ("ERROR DELETING LOGGED SALE DATA FOR BOOKID(<book_id>): <error>", "error") on SQLite error.

    Description:
        This function deletes records from the SalesLog table where ActiveBookID matches the given book_id
        and ReportID is 'Pending'. This is used to clear temporary log entries.
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


def update_pending_sales_log_report_id(database_path, report_id):
    """
    Updates all 'Pending' sales log entries by assigning them a specified ReportID.

    Parameters:
        database_path (str): The path to the SQLite database file.
        report_id (str or int): The ReportID to assign to all sales log entries currently marked as 'Pending'.

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


def update_sales_log_prev_TicketNum(
    database_path, prev_TicketNum, report_id, ActiveBookID
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
                (report_id, ActiveBookID),
            )

            row = cursor.fetchone()
            if row is None:
                return "NO MATCHING SALE ENTRY FOUND.", "error"

            current_TicketNum = int(row[0])
            counting_order = load_config()["ticket_order"]
            if counting_order == "descending":
                sold = int(prev_TicketNum) - int(current_TicketNum)
            else:
                sold = int(current_TicketNum) - int(prev_TicketNum)

            cursor.execute(
                """
            UPDATE SalesLog
            SET prev_TicketNum = ?, Ticket_Sold_Quantity = ?
            WHERE ReportID = ? AND ActiveBookID = ?;
            """,
                (prev_TicketNum, sold, report_id, ActiveBookID),
            )
    except sqlite3.Error as e:
        return f"ERROR UPDATING OPEN VALUE FOR LOGGED SALES: {e}", "error"


def update_sales_log_current_TicketNum(
    database_path, current_TicketNum, report_id, ActiveBookID
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
                (report_id, ActiveBookID),
            )

            row = cursor.fetchone()
            if row is None:
                return "NO MATCHING SALE ENTRY FOUND.", "error"

            prev_TicketNum = int(row[0])
            counting_order = load_config()["ticket_order"]
            if counting_order == "descending":
                sold = int(prev_TicketNum) - int(current_TicketNum)
            else:
                sold = int(current_TicketNum) - int(prev_TicketNum)

            cursor.execute(
                """
            UPDATE SalesLog
            SET current_TicketNum = ?, Ticket_Sold_Quantity = ?
            WHERE ReportID = ? AND ActiveBookID = ?;
            """,
                (current_TicketNum, sold, report_id, ActiveBookID),
            )
    except sqlite3.Error as e:
        return f"ERROR UPDATING OPEN VALUE FOR LOGGED SALES: {e}", "error"


def update_sale_report(
    database_path,
    instant_sold,
    online_sold,
    instant_cashed,
    online_cashed,
    cash_on_hand,
    report_id,
    date=datetime.datetime.now(datetime.timezone.utc).time().strftime("%H:%M:%S"),
):
    """
    Updates a finalized SaleReport entry with totals for ticket sales and cash.

    Parameters:
        database_path (str): Path to the SQLite database.
        instant_sold (int): Number of instant tickets sold.
        online_sold (int): Number of online tickets sold.
        instant_cashed (int): Number of instant tickets cashed.
        online_cashed (int): Number of online tickets cashed.
        cash_on_hand (float): Amount of cash on hand at the time of the report.
        report_id (str or int): The ReportID identifying the sale report.
        date (str, optional): Time of the report update. Defaults to current UTC time.

    Returns:
        tuple:
            - ("ERROR UPDATING SALE REPORT for REPORTID(<report_id>): <error>", "error") on failure.

    """
    initialize_database(database_path)
    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
                UPDATE SaleReport
                SET
                    InstantTicketSold = ?,
                    OnlineTicketSold = ?,
                    InstantTicketCashed = ?,
                    OnlineTicketCashed = ?,
                    CashOnHand = ?,
                    ReportTime = ?
                WHERE ReportID = ?
            """,
                (
                    instant_sold,
                    online_sold,
                    instant_cashed,
                    online_cashed,
                    cash_on_hand,
                    date,
                    report_id,
                ),
            )
    except sqlite3.Error as e:
        return f"ERROR UPDATING SALE REPORT for REPORTID({report_id}): {e}", "error"


def add_daily_totals(cursor, daily_totals):  # add_Sale_Report
    cursor.execute(
        """
        INSERT INTO SaleReport (
            ReportID,
            InstantTicketSold,
            OnlineTicketSold,
            InstantTicketCashed,
            OnlineTicketCashed,
            CashOnHand
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            daily_totals["ReportID"],
            daily_totals["instant_sold"],
            daily_totals["online_sold"],
            daily_totals["instant_cashed"],
            daily_totals["online_cashed"],
            daily_totals["cash_on_hand"],
        ),
    )


def insert_daily_totals(database_path, daily_totals):
    """
    Inserts a new daily total entry into the SaleReport table.

    Parameters:
        database_path (str): Path to the SQLite database.
        daily_totals (dict): Dictionary containing daily total values to be inserted.
                             Must include a 'ReportID' key.

    Returns:
        tuple:
            - ("ERROR ADDING A SALE REPORT FOR REPORTID(<ReportID>): <error>", "error") if an error occurs.
            - None if insertion is successful.

    Description:
        This function uses the provided `daily_totals` dictionary
        to add a new row to the SaleReport table using the helper function `add_daily_totals`.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            add_daily_totals(cursor, daily_totals)
    except sqlite3.Error as e:
        return (
            f"ERROR ADDING A SALE REPORT FOR REPORTID({daily_totals['ReportID']}): {e}",
            "error",
        )


def update_sale_report_instant_sold(database_path, instant_sold, report_id):
    """
    Updates the `InstantTicketSold` field for a specific sale report.

    Parameters:
        database_path (str): Path to the SQLite database.
        instant_sold (int): The updated number of instant tickets sold.
        report_id (str): The ReportID of the report to be updated.

    Returns:
        tuple:
            - ("ERROR UPDATING INSTANT SOLD VALUE FOR SALES REPORTID(<report_id>): <error>", "error") on SQLite error.

    Description:
        This function updates the `InstantTicketSold` field for the specified ReportID in the SaleReport table.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
            UPDATE SaleReport
            SET InstantTicketSold = ?
            WHERE ReportID = ?;
            """,
                (instant_sold, report_id),
            )
    except sqlite3.Error as e:
        return (
            f"Error updating instant sold value for sales reportid({report_id}) : ".upper()
            + f"{e}",
            "error",
        )


def update_pending_TicketTimeLine_report_id(database_path, report_id):
    """
    Updates all pending ticket timeline entries by assigning them the specified ReportID.

    Parameters:
        database_path (str): Path to the SQLite database.
        report_id (str): The ReportID to assign to all 'Pending' TicketTimeLine entries.

    Returns:
        tuple:
            - ("ERROR ADDING REPORTID(<report_id>) TO PENDING TICKET TIMELINE ENTRIES: <error>", "error") on SQLite error.

    Description:
        This function finds all rows in the TicketTimeLine table where the ReportID is currently 'Pending'
        and updates them with the specified ReportID, during report finalization.
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
            f"Error adding reportID({report_id}) to pending ticket timeline entires: ".upper()
            + f"{e}",
            "error",
        )


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
                "DELETE FROM ActivatedBooks WHERE ActiveBookID = ?;", (book_id,)
            )
    except sqlite3.Error as e:
        return "Error deactivating book: ".upper() + f"{e}", "error"


def update_isAtTicketNumber(database_path):
    """
    Sets the 'isAtTicketNumber' field to the value of 'countingTicketNumber' for all activated books.

    Parameters:
        database_path (str): Path to the SQLite database.

    Returns:
        tuple:
            - ("An error occurred while setting new open values for activated books: <error>", "error") on failure.

    Description:
        This function updates every row in ActivatedBooks so that isAtTicketNumber matches countingTicketNumber.
    """
    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute("""
                UPDATE ActivatedBooks
                SET isAtTicketNumber = countingTicketNumber
            """)
    except sqlite3.Error as e:
        return (
            "An error occured while setting new open values for activated books: ".upper()
            + f"{e}",
            "error",
        )


def update_isAtTicketNumber_val(database_path, bookID, newVal):
    """
    Updates the 'isAtTicketNumber' field for a single activated book to a new value.

    Parameters:
        database_path (str): Path to the SQLite database.
        bookID (str or int): The ActiveBookID to update.
        newVal (int): New value for isAtTicketNumber.

    Returns:
        tuple:
            - ("Error updating open value to <newVal> at bookID(<bookID>): <error>", "error") on failure.

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
                (newVal, bookID),
            )
    except sqlite3.Error as e:
        return (
            f"Error updating open value to {newVal} at bookID({bookID}): ".upper()
            + f"{e}",
            "error",
        )


def clear_countingTicketNumbers(database_path):
    """
    Clears the 'countingTicketNumber' field (sets to NULL) for all activated books records.

    Parameters:
        database_path (str): Path to the SQLite database.

    Returns:
        tuple:
            - ("An error occurred while clearing old closing values: <error>", "error") on failure.

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
            "An Error occured while clearing old closing values: ".upper() + f"{e}",
            "error",
        )


def clear_counting_ticket_number(database_path, book_id):
    """
    Clears the 'countingTicketNumber' field (sets to NULL) for a single activated book.

    Parameters:
        database_path (str): Path to the SQLite database.
        book_id (str): The ActiveBookID whose countingTicketNumber should be cleared.

    Returns:
        tuple:
            - ("Unable to clear closing value at bookID(<book_id>): <error>", "error") on failure.

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
            f"Unable to clear closing value at bookID({book_id})".upper() + f"{e}",
            "error",
        )


def insert_Ticket_name(database_path, ticket_name, ticket_gamenumber):
    """
    Inserts a new ticket name and its corresponding game number into the TicketNameLookup table.

    Parameters:
        database_path (str): Path to the SQLite database.
        ticket_name (str): The name of the ticket.
        ticket_gamenumber (str or int): The game number associated with the ticket.

    Returns:
        tuple:
            - ("Ticket Name insertion error: <error>", "error") on failure.

    Description:
        Adds a new entry mapping a ticket's game number to its name.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
                INSERT INTO TicketNameLookup (GameNumber, TicketName)
                VALUES (?, ?)
            """,
                (ticket_gamenumber, ticket_name),
            )
    except sqlite3.Error as e:
        return "Ticket Name insertion error: ".upper() + f"{e}", "error"


def delete_Book(database_path, book_id):
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


def update_ticketTimeline_ticketnumber(database_path, reportID, bookID, ticketNumber):
    """
    Updates the TicketNumber for a specific entry in the TicketTimeLine table.

    Parameters:
        database_path (str): Path to the SQLite database.
        reportID (str or int): The ReportID identifying the timeline entry.
        bookID (str or int): The BookID identifying the timeline entry.
        ticketNumber (int): The new ticket number to set.

    Returns:
        tuple:
            - ("Error updating TicketNumber in Timeline for (<reportID>, <bookID>): <error>", "error") on failure.

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
                (ticketNumber, reportID, bookID),
            )
    except sqlite3.Error as e:
        return (
            f"Error updating TicketNumber in Timeline for ({reportID}, {bookID}): ".upper()
            + f"{e}",
            "error",
        )
