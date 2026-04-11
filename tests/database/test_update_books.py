"""Tests for lottery_app.database.update_books."""

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
    """Test that a book can be inserted into the Books table."""
    _, status = insert_book_info_to_books_table(db_path, BOOK)
    assert status == "success"


def test_insert_duplicate_book(db_path):
    """Test that inserting a duplicate book returns an error with 'ALREADY' in the message."""
    insert_book_info_to_books_table(db_path, BOOK)
    msg, status = insert_book_info_to_books_table(db_path, BOOK)

    assert status == "error"
    assert "ALREADY" in msg


def test_update_is_sold_for_book(db_path):
    """Test that the Is_Sold flag can be updated for a book."""
    insert_book_info_to_books_table(db_path, BOOK)

    _, status = update_is_sold_for_book(db_path, 1, "BOOK1")
    assert status == "success"


def test_delete_book(db_path):
    """Test that a book can be deleted from the Books table."""
    insert_book_info_to_books_table(db_path, BOOK)

    _, status = delete_book(db_path, "BOOK1")
    assert status == "success"
