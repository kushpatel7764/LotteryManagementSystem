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
            "isAtTicketNumber": book[3],
            "created_at": book[4],
            "updated_at": book[5]
        })

    return books_list


    