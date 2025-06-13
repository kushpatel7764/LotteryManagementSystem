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
            """
            SELECT TicketNameLookup.TicketName, ActivatedBooks.ActiveBookID, Books.GameNumber, Books.Is_Sold, ActivatedBooks.isAtTicketNumber, ActivatedBooks.countingTicketNumber 
            FROM ActivatedBooks 
            Join Books ON ActiveBookID = BookID
            Left Join TicketNameLookup ON Books.GameNumber = TicketNameLookup.GameNumber;
            """
        )
        result_table = cursor.fetchall()
        result_row_list = []
        for table in result_table:
            result_row_list.append(
                {
                    "TicketName": table[0],
                    "ActiveBookID": table[1],
                    "GameNumber": table[2],
                    'Is_Sold': table[3],
                    "isAtTicketNumber": table[4],
                    "countingTicketNumber": table[5]
                }
            )
        
        return result_row_list

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

    finally:
        conn.close()
        
def get_all_instant_tickets_sold_quantity(db, ReportID):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        query = """
            SELECT SalesLog.ActiveBookID, SalesLog.Ticket_Sold_Quantity, Books.TicketPrice 
            FROM SalesLog 
            JOIN Books ON ActiveBookID = BookID 
            WHERE SalesLog.ReportID = ?;
        """
        cursor.execute(query, (ReportID, ))
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
    
def get_all_sold_books(db, ReportID):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT ActiveBookID, Ticket_Sold_Quantity, Books.TicketPrice 
            FROM SalesLog 
            JOIN Books ON ActiveBookID = BookID 
            WHERE ReportID = ? and Is_Sold = True;
        """
        cursor.execute(query, (ReportID,))
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
        
def get_table_for_invoice(db, ReportID):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT SalesLog.Ticket_Name, SalesLog.Ticket_GameNumber, SalesLog.ActiveBookID, Books.TicketPrice, SalesLog.prev_TicketNum, SalesLog.current_TicketNum, SalesLog.Ticket_Sold_Quantity
            FROM SalesLog
            Join Books ON ActiveBookID = BookID
            Where ReportID = ?
            ORDER BY Books.TicketPrice DESC;
        """
        cursor.execute(query, (ReportID,))
        result_table = cursor.fetchall()
        result_row_list = []
        for table in result_table:
            result_row_list.append(
                {
                    "TicketName": table[0],
                    "Ticket_GameNumber": table[1],
                    "ActiveBookID": table[2],
                    "TicketPrice": table[3],
                    "Open": table[4],
                    "Close": table[5],
                    "Sold": table[6]
                }
            )
        return result_row_list
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()
        
def get_daily_report(db, ReportID):
    # Not really daily report but a session report
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT *
            FROM SaleReport
            Where ReportID = ?;
        """
        cursor.execute(query, (ReportID,))
        result_table = cursor.fetchone()
        result_row = {
            "ReportID": result_table[0], 
            "ReportDate": result_table[1],
            "ReportTime": result_table[2], 
            "InstantTicketSold": result_table[3],
            "OnlineTicketSold": result_table[4],
            "InstantTicketCashed": result_table[5],
            "OnlineTicketCashed": result_table[6],
            "CashOnHand": result_table[7],
            "TotalDue": result_table[8]
        }
            
        return result_row
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_all_sales_reports(db):
     # Not really daily report but a session report
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT *
            FROM SaleReport;
        """
        cursor.execute(query)
        result_table = cursor.fetchall()
        result_row = []
        for row in result_table:
            result_row.append({
                "ReportID": row[0], 
                "ReportDate": row[1],
                "ReportTime": row[2], 
                "InstantTicketSold": row[3],
                "OnlineTicketSold": row[4],
                "InstantTicketCashed": row[5],
                "OnlineTicketCashed": row[6],
                "CashOnHand": row[7],
                "TotalDue": row[8]
            })
            
        return result_row
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()
    
def get_sales_log(db, ReportID):
     # Not really daily report but a session report
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT *
            FROM SalesLog
            Where ReportID = ?;
        """
        cursor.execute(query, (ReportID,))
        result_table = cursor.fetchall()
        result_rows = []
        for row in result_table:
            result_rows.append({
                "ActiveBookID": row[3],
                "Open": row[4],
                "Close": row[5],
                "Sold": row[6],
                "Game Name": row[7],
                "Game #": row[8]
            })
            
        return result_rows
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_gm_from_lookup(db):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT GameNumber
            FROM TicketNameLookup;
        """
        cursor.execute(query)
        result_table = cursor.fetchall()
        return result_table
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_ticket_name(db, game_number):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        
        query = """
            SELECT TicketName
            FROM TicketNameLookup
            Where GameNumber = ?;
        """
        cursor.execute(query, (game_number,))
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return "N/A"
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()
        
def next_report_ID(db):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        cursor.execute("SELECT ReportID FROM SaleReport ORDER BY ReportID DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            report_id = str(int(row[0]) + 1)
        else:
            report_id = "1"
        return report_id
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def can_Submit(db):
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()

        cursor.execute("SELECT countingTicketNumber FROM ActivatedBooks")
        rows = cursor.fetchall()
        
        if rows:
            for row in rows:
                if row[0] is None:
                    return False
            return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()