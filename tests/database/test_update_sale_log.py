import sqlite3
from lottery_app.database.update_sale_log import (
    insert_sales_log,
    delete_sales_log_by_book_id,
    update_pending_sales_log_report_id,
    update_sales_log_prev_ticketnum,
    update_sales_log_current_ticketnum,
)
from lottery_app.decorators import get_db_cursor


def test_insert_sales_log_pending(temp_db, sample_ticket_info):
    msg, status = insert_sales_log(temp_db, sample_ticket_info)

    assert status == "success"

    with get_db_cursor(temp_db) as cursor:
        cursor.execute("SELECT * FROM SalesLog;")
        rows = cursor.fetchall()

    assert len(rows) == 1
    assert rows[0]["ActiveBookID"] == "BOOK123"
    assert rows[0]["ReportID"] == "Pending"
    # assert rows[0][0] == "BOOK123"   # ActiveBookID
    # assert rows[0][1] == "Pending"  # ReportID


def test_insert_sales_log_with_report_id(temp_db, sample_ticket_info):
    sample_ticket_info["ReportID"] = "R1"

    msg, status = insert_sales_log(temp_db, sample_ticket_info)
    assert status == "success"

    with get_db_cursor(temp_db) as cursor:
        cursor.execute("SELECT ReportID FROM SalesLog;")
        report_id = cursor.fetchone()[0]

    assert report_id == "R1"


def test_delete_sales_log_by_book_id(temp_db, sample_ticket_info):
    insert_sales_log(temp_db, sample_ticket_info)

    msg, status = delete_sales_log_by_book_id(temp_db, "BOOK123")
    assert status == "success"

    with get_db_cursor(temp_db) as cursor:
        cursor.execute("SELECT * FROM SalesLog;")
        assert cursor.fetchall() == []


def test_update_pending_sales_log_report_id(temp_db, sample_ticket_info):
    insert_sales_log(temp_db, sample_ticket_info)

    msg, status = update_pending_sales_log_report_id(temp_db, "R99")
    assert status == "success"

    with get_db_cursor(temp_db) as cursor:
        cursor.execute("SELECT ReportID FROM SalesLog;")
        assert cursor.fetchone()[0] == "R99"


def test_update_sales_log_prev_ticketnum_success(temp_db, sample_ticket_info):
    sample_ticket_info["ReportID"] = "R2"
    insert_sales_log(temp_db, sample_ticket_info)

    msg, status = update_sales_log_prev_ticketnum(
        temp_db, prev_ticketnum=110, report_id="R2", active_book_id="BOOK123"
    )

    assert status == "success"


def test_update_sales_log_prev_ticketnum_no_match(temp_db):
    msg, status = update_sales_log_prev_ticketnum(
        temp_db, prev_ticketnum=100, report_id="BAD", active_book_id="NONE"
    )

    assert status == "warning"


def test_update_sales_log_current_ticketnum_success(temp_db, sample_ticket_info):
    sample_ticket_info["ReportID"] = "R3"
    insert_sales_log(temp_db, sample_ticket_info)

    msg, status = update_sales_log_current_ticketnum(
        temp_db, current_ticketnum=80, report_id="R3", active_book_id="BOOK123"
    )

    assert status == "success"