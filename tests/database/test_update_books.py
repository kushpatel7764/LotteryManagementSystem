from lottery_app.database.update_books import (
    insert_book_info_to_books_table,
    update_is_sold_for_book,
    delete_book,
)

BOOK = {
    "BookID": "BOOK1",
    "GameNumber": "G1",
    "Is_Sold": 0,
    "BookAmount": 100,
    "TicketPrice": 5.0,
}


def test_insert_book_success(db_path):
    msg, status = insert_book_info_to_books_table(db_path, BOOK)
    assert status == "success"


def test_insert_duplicate_book(db_path):
    insert_book_info_to_books_table(db_path, BOOK)
    msg, status = insert_book_info_to_books_table(db_path, BOOK)

    assert status == "error"
    assert "ALREADY" in msg


def test_update_is_sold_for_book(db_path):
    insert_book_info_to_books_table(db_path, BOOK)

    msg, status = update_is_sold_for_book(db_path, 1, "BOOK1")
    assert status == "success"


def test_delete_book(db_path):
    insert_book_info_to_books_table(db_path, BOOK)

    msg, status = delete_book(db_path, "BOOK1")
    assert status == "success"
