"""Tests for lottery_app.database.update_ticket_timeline."""

import sqlite3
from unittest.mock import patch, MagicMock

import pytest

from lottery_app.database.update_ticket_timeline import (
    add_ticket_to_timeline,
    add_ticket_to_timeline_at_report_id,
    insert_ticket_to_ticket_timeline_table,
    delete_ticket_timeline_by_book_id,
    update_pending_ticket_timeline_report_id,
    update_ticket_timeline_ticketnumber,
)

# pylint: disable=redefined-outer-name

# --------------------------
# Fixtures
# --------------------------


@pytest.fixture
def mock_cursor():
    """Return a MagicMock to stand in for an SQLite cursor."""
    return MagicMock()


@pytest.fixture
def ticket_info():
    """Return a basic ticket info dict without a ReportID."""
    return {
        "ScanID": "SCAN1",
        "BookID": "BOOK1",
        "TicketNumber": 5,
        "TicketName": "Mega",
        "TicketPrice": 10,
    }


@pytest.fixture
def ticket_info_with_report(ticket_info):
    """Return a ticket info dict that includes a ReportID."""
    ticket_info["ReportID"] = "R1"
    return ticket_info


# --------------------------
# add_ticket_to_timeline
# --------------------------


def test_add_ticket_to_timeline_executes_query(mock_cursor, ticket_info):
    """Test that add_ticket_to_timeline calls cursor.execute exactly once."""
    add_ticket_to_timeline(mock_cursor, ticket_info)

    mock_cursor.execute.assert_called_once()


# --------------------------
# add_ticket_to_timeline_at_report_id
# --------------------------


def test_add_ticket_to_timeline_at_report_id_executes_query(
    mock_cursor, ticket_info_with_report
):
    """Test that add_ticket_to_timeline_at_report_id calls cursor.execute exactly once."""
    add_ticket_to_timeline_at_report_id(mock_cursor, ticket_info_with_report)

    mock_cursor.execute.assert_called_once()


# --------------------------
# insert_ticket_to_ticket_timeline_table
# --------------------------


@patch("lottery_app.database.update_ticket_timeline.initialize_database")
@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_insert_ticket_without_report_id(mock_cursor_ctx, _mock_init, ticket_info):
    """Test successful insertion of a ticket without a ReportID."""
    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    message, status = insert_ticket_to_ticket_timeline_table("test.db", ticket_info)

    assert status == "success"
    assert "SUCCESSFULLY" in message


@patch("lottery_app.database.update_ticket_timeline.initialize_database")
@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_insert_ticket_with_report_id(
    mock_cursor_ctx, _mock_init, ticket_info_with_report
):
    """Test successful insertion of a ticket that includes a ReportID."""
    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    _, status = insert_ticket_to_ticket_timeline_table(
        "test.db", ticket_info_with_report
    )

    assert status == "success"


@patch("lottery_app.database.update_ticket_timeline.initialize_database")
@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_insert_ticket_integrity_error(mock_cursor_ctx, _mock_init, ticket_info):
    """Test that an IntegrityError returns an error status with the correct message."""
    mock_cursor_ctx.side_effect = sqlite3.IntegrityError("duplicate")

    message, status = insert_ticket_to_ticket_timeline_table("test.db", ticket_info)

    assert status == "error"
    assert "INTEGRITY ERROR" in message


@patch("lottery_app.database.update_ticket_timeline.initialize_database")
@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_insert_ticket_general_sql_error(mock_cursor_ctx, _mock_init, ticket_info):
    """Test that a generic sqlite3.Error returns an error status with the correct message."""
    mock_cursor_ctx.side_effect = sqlite3.Error("db error")

    message, status = insert_ticket_to_ticket_timeline_table("test.db", ticket_info)

    assert status == "error"
    assert "ERROR INSERTING" in message


# --------------------------
# delete_ticket_timeline_by_book_id
# --------------------------


@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_delete_ticket_timeline_success(mock_cursor_ctx):
    """Test that deleting a ticket timeline entry succeeds."""
    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    _, status = delete_ticket_timeline_by_book_id("db", "BOOK1")

    assert status == "success"


@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_delete_ticket_timeline_error(mock_cursor_ctx):
    """Test that a DB error during deletion returns an error status."""
    mock_cursor_ctx.side_effect = sqlite3.Error("failure")

    message, status = delete_ticket_timeline_by_book_id("db", "BOOK1")

    assert status == "error"
    assert "ERROR DELETING" in message


# --------------------------
# update_pending_ticket_timeline_report_id
# --------------------------


@patch("lottery_app.database.update_ticket_timeline.initialize_database")
@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_update_pending_success(mock_cursor_ctx, _mock_init):
    """Test that updating the pending report ID succeeds."""
    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    _, status = update_pending_ticket_timeline_report_id("db", "R1")

    assert status == "success"


@patch("lottery_app.database.update_ticket_timeline.initialize_database")
@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_update_pending_error(mock_cursor_ctx, _mock_init):
    """Test that a DB error during pending update returns an error status."""
    mock_cursor_ctx.side_effect = sqlite3.Error("failure")

    _, status = update_pending_ticket_timeline_report_id("db", "R1")

    assert status == "error"


# --------------------------
# update_ticket_timeline_ticketnumber
# --------------------------


@patch("lottery_app.database.update_ticket_timeline.initialize_database")
@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_update_ticketnumber_success(mock_cursor_ctx, _mock_init):
    """Test that updating a ticket number in the timeline succeeds."""
    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    _, status = update_ticket_timeline_ticketnumber("db", "R1", "BOOK1", 10)

    assert status == "success"


@patch("lottery_app.database.update_ticket_timeline.initialize_database")
@patch("lottery_app.database.update_ticket_timeline.get_db_cursor")
def test_update_ticketnumber_error(mock_cursor_ctx, _mock_init):
    """Test that a DB error during ticket number update returns an error status."""
    mock_cursor_ctx.side_effect = sqlite3.Error("failure")

    _, status = update_ticket_timeline_ticketnumber("db", "R1", "BOOK1", 10)

    assert status == "error"
