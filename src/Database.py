import os
import sqlite3
import datetime

# Connect to database
def setup_database_schema_with_sql_file(cursor, conn, sql_filename):
    
    setup_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves up one level
    sql_file_path = os.path.join(setup_dir, sql_filename)

    # Read the SQL schema file
    with open(sql_file_path, "r") as file:
        sql_script = file.read()

    cursor.executescript(sql_script)
    conn.commit()

def initialize_database(database_path):
    
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    setup_database_schema_with_sql_file(cursor, conn, "Lottery_DB_Schema.sql")
    conn.close()


def add_book(conn, cursor, book_info):
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
    cursor.execute("""
        INSERT INTO Books (BookID, GameNumber, Is_Sold, BookAmount, TicketPrice)
        VALUES (?, ?, ?, ?, ?)
    """, (
        book_info["BookID"],
        book_info["GameNumber"],
        book_info["Is_Sold"], 
        book_info["BookAmount"],
        book_info["TicketPrice"]
    ))

    conn.commit()

def insert_book_info_to_Books_table(database_path, book_info):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    try:
        add_book(conn, cursor, book_info)
    except sqlite3.Error as e:
        print(f"Error adding book to the database: {e}")

    print("book data successfully inserted!")
    conn.close()
    
def add_ticket_to_timeline(conn, cursor, ticket_info):
    """
    Inserts a ticket record into the database.

    Parameters:
        ticket_info (dict): A dictionary with keys:
            - ScanID
            - BookID
            - TicketNumber
            - TicketName
            - TicketPrice
    """
    cursor.execute("""
        INSERT INTO TicketTimeline (ScanID, BookID, TicketNumber, TicketName, TicketPrice)
        VALUES (?, ?, ?, ?, ?)
    """, (
        ticket_info["ScanID"],
        ticket_info["BookID"],
        ticket_info["TicketNumber"],
        ticket_info["TicketName"],
        ticket_info["TicketPrice"]
    ))

    conn.commit()

def set_updated_time_in_timeline(conn, cursor, scanID, updated_time):
    cursor.execute("""
                UPDATE TicketTimeline
                SET updated_time = ?
                WHERE scanID = ?;
                   """, (updated_time, scanID))
    conn.commit()
    
def insert_ticket_to_TicketTimeline_table(database_path, ticket_info):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    try:
        add_ticket_to_timeline(conn, cursor, ticket_info)
    except sqlite3.IntegrityError as e: 
        if "UNIQUE constraint failed" in str(e):
            # the updated_time attribute should now be updated to new utc time.
            set_updated_time_in_timeline(conn, cursor, ticket_info["ScanID"], datetime.datetime.now(datetime.timezone.utc).time().strftime("%H:%M:%S"))
        else:
            print("Integrity error:", e)
    except sqlite3.Error as e:
        print(f"Error inserting ticket to TicketTimeLine: {e}")

    print("Ticket data successfully inserted!")
    conn.close()
    
    
def add_activate_book_info_to_Activated_Book(conn, cursor, activated_book_info):
    """
    Inserts a book into the ActivatedBooks table.

    Parameters:
        activated_book_info (dict): A dictionary with keys:
            - ActivationID
            - ActiveBookID
            - Is_Sold
            - isAtTicketNumber
    """
    cursor.execute("""
        INSERT INTO ActivatedBooks (ActivationID, ActiveBookID, isAtTicketNumber)
        VALUES (?, ?, ?)
    """, (
        activated_book_info["ActivationID"],
        activated_book_info["ActiveBookID"],
        activated_book_info["isAtTicketNumber"]
    ))

    conn.commit()
    
def insert_book_to_ActivatedBook_table(database_path, active_book_info):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    try:
        add_activate_book_info_to_Activated_Book(conn, cursor, active_book_info)
    except sqlite3.Error as e:
        print(f"Error Activating the book: {e}")
    
    print("book activated successfully!")
    conn.close()

def update_counting_ticket_number_for_book_id_query(cursor, conn, book_id, new_ticket_number): 
    # SQL query to update the countingTicketNumber
    update_query = '''
    UPDATE ActivatedBooks
    SET countingTicketNumber = ?
    WHERE ActiveBookID = ?;
    '''
    # Execute the update query
    cursor.execute(update_query, (new_ticket_number, book_id))

    # Commit changes and close the connection
    conn.commit()
    
def update_counting_ticket_number(database_path, book_id, new_ticket_number):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    try:
        update_counting_ticket_number_for_book_id_query(cursor, conn, book_id, new_ticket_number)
    except sqlite3.Error as e:
        print(f"Error updating counting_ticket_number: {e}")
    
    conn.close()
    
def book_is_sold(cursor, conn, book_id):
    cursor.execute("""
        UPDATE Books
        SET Is_Sold = True
        WHERE BookID = ?
    """, (book_id,))
    
    conn.commit()
    
def update_is_sold_for_book(database_path, book_id):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    try:
        book_is_sold(cursor, conn, book_id)
    except sqlite3.Error as e:
        print(f"Error updating is_sold: {e}")
    
    conn.close()
    
def add_sales_log (cursor, conn, scanned_ticket_info):
    
    """
    ActiveBookID VARCHAR(255),
    prev_TicketNum INTEGER,
    current_TicketNum INTEGER,
    Ticket_Sold_Quantity INTEGER,
    Ticket_Name TEXT,
    Ticket_GameNumber VARCHAR(255),
    """
    cursor.execute("""
                   INSERT INTO SalesLog (ActiveBookID, prev_TicketNum, current_TicketNum, Ticket_Sold_Quantity, Ticket_Name, Ticket_GameNumber)
                   VALUES (?, ?, ?, ?, ?, ?)
                   """, (scanned_ticket_info["ActiveBookID"], scanned_ticket_info["prev_TicketNum"], scanned_ticket_info["current_TicketNum"], scanned_ticket_info["Ticket_Sold_Quantity"], scanned_ticket_info["Ticket_Name"],
                        scanned_ticket_info["Ticket_GameNumber"]))
    
    conn.commit()
    
def insert_sales_log (database_path, scanned_ticket_info):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    try:
        add_sales_log(cursor, conn, scanned_ticket_info)
    except sqlite3.Error as e:
        print(f"SalesLog error: {e}")
    
    conn.close()
    
def add_daily_totals(cursor, conn, daily_totals):
    cursor.execute('''
        INSERT INTO SaleReport (
            ReportID,
            InstantTicketSold,
            OnlineTicketSold,
            InstantTicketCashed,
            OnlineTicketCashed,
            CashOnHand,
            TotalDue
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        daily_totals['ReportID'],
        daily_totals['instant_sold'],
        daily_totals['online_sold'],
        daily_totals['instant_cashed'],
        daily_totals['online_cashed'],
        daily_totals['cash_on_hand'],
        daily_totals["total_due"],
    ))

    conn.commit()

def insert_daily_totals(db_path, daily_totals):
    initialize_database(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        add_daily_totals(cursor, conn, daily_totals)
    except sqlite3.Error as e:
        print(f"Daily total insertion error: {e}")
        
    conn.close()
    
def update_pending_sales_log_report_id(db_path, report_id):
    initialize_database(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE SalesLog
        SET ReportID = ?
        WHERE ReportID = 'Pending';
        """, (report_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating pending sales log: {e}")
        
    conn.close()
    
def deactivate_book(db_path, book_id):
    initialize_database(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM ActivatedBooks WHERE ActiveBookID = ?;", (book_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error deactivating book: {e}")
    
    conn.close()
    
def update_isAtTicketNumber(db_path):
    # Connect to your database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Update each row: set isAtTicketNumber = countingTicketNumber
        cursor.execute('''
            UPDATE ActivatedBooks
            SET isAtTicketNumber = countingTicketNumber
        ''')

        # Commit changes and close connection
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error updating isAtTicketNumber: {e}")

    conn.close()
    
def clear_countingTicketNumber(db_path):
    # Connect to your database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Update each row: set isAtTicketNumber = countingTicketNumber
        cursor.execute('''
            UPDATE ActivatedBooks
            SET countingTicketNumber = NULL
        ''')

        # Commit changes and close connection
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error updating isAtTicketNumber: {e}")

    conn.close()
    
def insert_Ticket_name(db_path, ticket_name, ticket_gamenumber):
    initialize_database(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO TicketNameLookup (GameNumber, TicketName)
            VALUES (?, ?)
        """, (ticket_gamenumber,ticket_name))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Ticket Name insertion error: {e}")
        
    conn.close()

def delete_Book(db_path, book_id):
    initialize_database(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM Books Where BookID = ?;
        """, (book_id,))

        conn.commit()
    except sqlite3.Error as e:
        print(f"Book deletion error: {e}")
        
    conn.close()