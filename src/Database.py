import os
import sqlite3

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
    """
    cursor.execute("""
        INSERT INTO Books (BookID, GameNumber, BookAmount)
        VALUES (?, ?, ?)
    """, (
        book_info["BookID"],
        book_info["GameNumber"],
        book_info["BookAmount"]
    ))

    conn.commit()

def insert_book_info_to_Books_table(database_path, book_info):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    try:
        add_book(conn, cursor, book_info)
    except sqlite3.Error as e:
        print(f"Database error: {e}")

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
    
def insert_ticket_to_TicketTimeline_table(database_path, ticket_info):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    try:
        add_ticket_to_timeline(conn, cursor, ticket_info)
    except sqlite3.Error as e:
        print(f"Database error: {e}")

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
        INSERT INTO ActivatedBooks (ActivationID, ActiveBookID, Is_Sold, isAtTicketNumber)
        VALUES (?, ?, ?, ?)
    """, (
        activated_book_info["ActivationID"],
        activated_book_info["ActiveBookID"],
        activated_book_info["Is_Sold"],
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
        print(f"Database error: {e}")
    
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
        print(f"Database error: {e}")
    
    conn.close()
    
def book_is_sold(cursor, conn, book_id):
    cursor.execute("""
        UPDATE ActivatedBooks
        SET Is_Sold = True
        WHERE book_id = ?
    """, (book_id,))
    
    conn.commit()
    
def update_is_sold_for_book(database_path, book_id):
    
    initialize_database(database_path)
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    try:
        book_is_sold(cursor, conn, book_id)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    
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
        print(f"Database error: {e}")
    
    conn.close()

