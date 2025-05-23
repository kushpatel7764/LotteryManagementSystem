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
            "isAtTicketNumber": book[3]
        })
    return activated_books_list

def get_book(db, book_id):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Books WHERE BookID = ? LIMIT 1;", (book_id,))
    book_id_exist = cursor.fetchone() is not None
    conn.close()
    
    if book_id_exist:
        return book_id_exist
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


    