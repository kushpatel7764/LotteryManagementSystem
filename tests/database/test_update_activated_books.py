"""Tests for lottery_app.database.update_activated_books."""

import sqlite3

from lottery_app.database.setup_database import initialize_database
from lottery_app.database.update_activated_books import (
    insert_book_to_activated_book_table,
    update_counting_ticket_number,
    deactivate_book,
    update_is_at_ticketnumbers,
    clear_counting_ticket_number,
    update_box_number,
)


def test_insert_activated_book_success(db_path):
    """Test that a book can be inserted into the ActivatedBooks table."""
    _, status = insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A1",
            "ActiveBookID": "B1",
            "isAtTicketNumber": 0,
        },
    )

    assert status == "success"

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT * FROM ActivatedBooks WHERE ActiveBookID = 'B1'"
    ).fetchone()
    conn.close()

    assert row is not None


def test_update_counting_ticket_number(db_path):
    """Test that the counting ticket number can be updated for an activated book."""
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A2",
            "ActiveBookID": "B2",
            "isAtTicketNumber": 0,
        },
    )

    _, status = update_counting_ticket_number(db_path, "B2", 50)
    assert status == "success"


def test_deactivate_book(db_path):
    """Test that a book can be deactivated successfully."""
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A3",
            "ActiveBookID": "B3",
            "isAtTicketNumber": 10,
        },
    )

    _, status = deactivate_book(db_path, "B3")
    assert status == "success"


def test_update_is_at_ticketnumbers(db_path):
    """Test that isAtTicketNumber values can be bulk-updated."""
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A4",
            "ActiveBookID": "B4",
            "isAtTicketNumber": 5,
        },
    )

    _, status = update_is_at_ticketnumbers(db_path)
    assert status == "success"


def test_clear_counting_ticket_number(db_path):
    """Test that the counting ticket number can be cleared for an activated book."""
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A5",
            "ActiveBookID": "B5",
            "isAtTicketNumber": 1,
        },
    )

    _, status = clear_counting_ticket_number(db_path, "B5")
    assert status == "success"


def test_update_box_number(db_path):
    """Test that an activated book can be moved to a different box."""
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A6",
            "ActiveBookID": "B6",
            "isAtTicketNumber": 0,
            "BoxNumber": "1",
        },
    )

    _, status = update_box_number(db_path, "B6", "5")
    assert status == "success"

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT BoxNumber FROM ActivatedBooks WHERE ActiveBookID = 'B6'"
    ).fetchone()
    conn.close()
    assert row[0] == "5"


def test_update_box_number_not_activated(db_path):
    """Test that reassigning the box of a non-activated book returns an error."""
    initialize_database(db_path)
    message, status = update_box_number(db_path, "MISSING", "5")
    assert status == "error"
    assert message == "BOOK IS NOT ACTIVATED!"
