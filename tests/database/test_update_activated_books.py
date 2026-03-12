import sqlite3

from lottery_app.database.update_activated_books import (
    insert_book_to_activated_book_table,
    update_counting_ticket_number,
    deactivate_book,
    update_is_at_ticketnumbers,
    update_is_at_ticketnumber_val,
    clear_counting_ticket_numbers,
    clear_counting_ticket_number,
)


def test_insert_activated_book_success(db_path):
    msg, status = insert_book_to_activated_book_table(
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
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A2",
            "ActiveBookID": "B2",
            "isAtTicketNumber": 0,
        },
    )

    msg, status = update_counting_ticket_number(db_path, "B2", 50)
    assert status == "success"


def test_deactivate_book(db_path):
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A3",
            "ActiveBookID": "B3",
            "isAtTicketNumber": 10,
        },
    )

    msg, status = deactivate_book(db_path, "B3")
    assert status == "success"


def test_update_is_at_ticketnumbers(db_path):
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A4",
            "ActiveBookID": "B4",
            "isAtTicketNumber": 5,
        },
    )

    msg, status = update_is_at_ticketnumbers(db_path)
    assert status == "success"


def test_clear_counting_ticket_number(db_path):
    insert_book_to_activated_book_table(
        db_path,
        {
            "ActivationID": "A5",
            "ActiveBookID": "B5",
            "isAtTicketNumber": 1,
        },
    )

    msg, status = clear_counting_ticket_number(db_path, "B5")
    assert status == "success"