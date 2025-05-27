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
            "BookAmount": book[2],
            "created_at": book[3],
            "updated_at": book[4]
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
            "Is_Sold": book[2],
            "isAtTicketNumber": book[3],
            "countingTicketNumber": book[4]
        })
    return activated_books_list

def get_book(db, book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Books WHERE BookID = ? LIMIT 1;", (book_id,))
    book = cursor.fetchone() is not None
    conn.close()
    
    if book:
        return book
    else:
        return False
    
def get_activated_book(db, activated_book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ActivatedBooks WHERE ActiveBookID = ? LIMIT 1;", (activated_book_id,))
    activated_book_id_exist = cursor.fetchone() is not None
    conn.close()
    
    if activated_book_id_exist:
        return activated_book_id_exist
    else:
        return False

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
            "SELECT ActivatedBooks.ActiveBookID, Books.GameNumber, ActivatedBooks.isAtTicketNumber, ActivatedBooks.countingTicketNumber FROM ActivatedBooks Join Books ON ActiveBookID = BookID;"
        )
        result_table = cursor.fetchall()
        result_row_list = []
        for table in result_table:
            result_row_list.append(
                {
                    "ActiveBookID": table[0],
                    "GameNumber": table[1],
                    "isAtTicketNumber": table[2],
                    "countingTicketNumber": table[3]
                }
            )
        
        return result_row_list

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None

    finally:
        conn.close()
