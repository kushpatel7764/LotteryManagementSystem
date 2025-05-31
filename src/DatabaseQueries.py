import sqlite3

def get_books(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Books")
    books = cursor.fetchall()
    conn.close()
    books_list = []
    for book in books:
        books_list.append({
            "BookID": book[0],
            "GameNumber": book[1],
            "Is_Sold": book[2],
            "BookAmount": book[3],
            "TicketPrice": book[4],
            "created_at": book[5],
            "updated_at": book[6]
        })

    return books_list

def get_activated_books(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ActivatedBooks")
    activated_books = cursor.fetchall()
    conn.close()
    activated_books_list = []
    for book in activated_books:
        activated_books_list.append({
            "ActivationID": book[0],
            "ActiveBookID": book[1],
            "isAtTicketNumber": book[3],
            "countingTicketNumber": book[4]
        })
    return activated_books_list

def is_book(db, book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Books WHERE BookID = ? LIMIT 1;", (book_id,))
    book = cursor.fetchone() is not None
    conn.close()
    
    if book:
        return book
    else:
        return False
    
def is_activated_book(db, activated_book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ActivatedBooks WHERE ActiveBookID = ? LIMIT 1;", (activated_book_id,))
    activated_book_id_exist = cursor.fetchone() is not None
    conn.close()
    
    if activated_book_id_exist:
        return activated_book_id_exist
    else:
        return False
    
def get_activated_book_isAtTicketNumber(db, activated_book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT isAtTicketNumber FROM ActivatedBooks WHERE ActiveBookID = ? LIMIT 1;", (activated_book_id,))
    activated_book_isAtTicketNumber = cursor.fetchone()
    conn.close()
    
    return activated_book_isAtTicketNumber

def get_activated_book(db, activated_book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ActivatedBooks WHERE ActiveBookID = ? LIMIT 1;", (activated_book_id,))
    activated_book = cursor.fetchone()
    conn.close()
    
    return activated_book

def get_book(db, book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Books WHERE BookID = ? LIMIT 1;", (book_id,))
    book = cursor.fetchone()
    conn.close()
    
    return book

def get_ticket_with_bookid(db, book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM TicketTimeLine WHERE BookID = ? LIMIT 1;", (book_id,))
    book = cursor.fetchone()
    conn.close()
    
    return book

def get_all_active_book_ids(db):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT ActiveBookID FROM ActivatedBooks")
    # Fetch all results
    active_book_ids = cursor.fetchall()
    # Optionally, flatten the result if you just want a list of IDs
    active_book_ids = [row[0] for row in active_book_ids]
    conn.close()
    return active_book_ids

def get_scan_ticket_page_table(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT ActivatedBooks.ActiveBookID, Books.GameNumber, Books.Is_Sold, ActivatedBooks.isAtTicketNumber, ActivatedBooks.countingTicketNumber FROM ActivatedBooks Join Books ON ActiveBookID = BookID;"
        )
        result_table = cursor.fetchall()
        result_row_list = []
        for table in result_table:
            result_row_list.append(
                {
                    "ActiveBookID": table[0],
                    "GameNumber": table[1],
                    'Is_Sold': table[2],
                    "isAtTicketNumber": table[3],
                    "countingTicketNumber": table[4]
                }
            )
        
        return result_row_list

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

    finally:
        conn.close()
        
def get_all_instant_tickets_sold_quantity(db, Date):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        query = """
            SELECT ActiveBookID, Ticket_Sold_Quantity, Books.TicketPrice 
            FROM SalesLog 
            JOIN Books ON ActiveBookID = BookID 
            WHERE SaleDate = ?;
        """
        cursor.execute(query, (Date,))
        result_table = cursor.fetchall()
        result_row_list = []
        for table in result_table:
            result_row_list.append(
                {
                    "ActiveBookID": table[0],
                    "Ticket_Sold_Quantity": table[1],
                    "TicketPrice": table[2]
                }
            )
        
        return result_row_list
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()
    
def get_all_sold_books(db):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT ActiveBookID, Ticket_Sold_Quantity, Books.TicketPrice 
            FROM SalesLog 
            JOIN Books ON ActiveBookID = BookID 
            WHERE SaleDate = ?;
        """
        cursor.execute(query)
        result_table = cursor.fetchall()
        result_row_list = []
        for table in result_table:
            result_row_list.append(
                {
                    "BookID": table[0]
                }
            )
        return result_row_list
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()
        
def get_table_for_invoice(db):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT SalesLog.TicketName, SalesLog.Ticket_GameNumber, SalesLog.ActiveBookID, Books.TicketPrice, SalesLog.prev_TicketNum, SalesLog.current_TicketNum, SalesLog.Ticket_Sold_Quantity
            FROM SalesLog
            Join Books ON ActiveBookID = BookID
            Where Date = ?;
        """
        cursor.execute(query)
        result_table = cursor.fetchall()
        result_row_list = []
        for table in result_table:
            result_row_list.append(
                {
                    "BookID": table[0]
                }
            )
        return result_row_list
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()