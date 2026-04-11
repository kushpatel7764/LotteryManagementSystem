# pylint: disable=redefined-outer-name
"""Tests for report utilities: calculate_instant_tickets_sold, create_daily_invoice,
add_sales_log, and do_submit_procedure in lottery_app.utils.reports."""
from datetime import datetime
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest
from flask import Flask

import lottery_app.utils.reports as reports_utils
from lottery_app.utils.reports import do_submit_procedure


# Patch db_path for every test in this module
@pytest.fixture(autouse=True)
def fake_db_path(monkeypatch):
    """Replace the module-level db_path with a dummy value."""
    monkeypatch.setattr(reports_utils, "db_path", "fake.db")


# ============================================================
# calculate_instant_tickets_sold tests
# ============================================================

def test_calculate_instant_tickets_sold_success(monkeypatch):
    """Happy path: quantities * prices are summed correctly."""
    fake_data = [
        {"Ticket_Sold_Quantity": 10, "TicketPrice": 2.0},
        {"Ticket_Sold_Quantity": 5, "TicketPrice": 3.0},
    ]

    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_all_instant_tickets_sold_quantity",
        lambda db, report_id: fake_data,
    )

    monkeypatch.setattr(
        reports_utils, "check_error", lambda result, msg_data, fallback: result
    )

    total = reports_utils.calculate_instant_tickets_sold("r1")

    assert total == (10 * 2.0 + 5 * 3.0)


def test_calculate_instant_tickets_sold_empty(monkeypatch):
    """An empty ticket list returns 0."""
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_all_instant_tickets_sold_quantity",
        lambda db, report_id: [],
    )

    monkeypatch.setattr(
        reports_utils, "check_error", lambda result, msg_data, fallback: []
    )

    total = reports_utils.calculate_instant_tickets_sold("r1")

    assert total == 0


def test_calculate_instant_tickets_sold_check_error_fallback(monkeypatch):
    """A DB error tuple causes check_error to return the fallback (0)."""
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_all_instant_tickets_sold_quantity",
        lambda db, report_id: ("DB error", "error"),
    )

    monkeypatch.setattr(
        reports_utils, "check_error", lambda result, msg_data, fallback: fallback
    )

    total = reports_utils.calculate_instant_tickets_sold("r1")

    assert total == 0


def test_calculate_instant_tickets_sold_invalid_ticket_data(monkeypatch):
    """A non-dict entry in the ticket list returns an error tuple."""
    fake_data = [
        {"Ticket_Sold_Quantity": 1, "TicketPrice": 2},
        "not-a-dict",
    ]

    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_all_instant_tickets_sold_quantity",
        lambda db, report_id: fake_data,
    )

    monkeypatch.setattr(
        reports_utils, "check_error", lambda result, msg_data, fallback: result
    )

    result = reports_utils.calculate_instant_tickets_sold("r1")

    assert result == ("ERROR: Invalid ticket sold data", "error")


def test_calculate_instant_tickets_sold_missing_keys(monkeypatch):
    """Missing keys in a ticket dict default to 0, so the total is 0."""
    fake_data = [
        {},
        {"Ticket_Sold_Quantity": 5},
        {"TicketPrice": 10},
    ]

    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_all_instant_tickets_sold_quantity",
        lambda db, report_id: fake_data,
    )

    monkeypatch.setattr(
        reports_utils, "check_error", lambda result, msg_data, fallback: result
    )

    total = reports_utils.calculate_instant_tickets_sold("r1")

    assert total == 0


def test_calculate_instant_tickets_sold_type_error(monkeypatch):
    """A non-numeric quantity causes a TypeError which is caught and returns 0."""
    fake_data = [
        {"Ticket_Sold_Quantity": "ten", "TicketPrice": 2},
    ]

    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_all_instant_tickets_sold_quantity",
        lambda db, report_id: fake_data,
    )

    monkeypatch.setattr(
        reports_utils, "check_error", lambda result, msg_data, fallback: result
    )

    total = reports_utils.calculate_instant_tickets_sold("r1")

    assert total == 0


def test_calculate_instant_tickets_sold_non_iterable(monkeypatch):
    """A non-iterable return from the DB raises TypeError."""
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_all_instant_tickets_sold_quantity",
        lambda db, report_id: 123,
    )

    monkeypatch.setattr(
        reports_utils, "check_error", lambda result, msg_data, fallback: result
    )

    with pytest.raises(TypeError):
        reports_utils.calculate_instant_tickets_sold("r1")


# ============================================================
# create_daily_invoice fixtures
# ============================================================


@pytest.fixture
def fixed_datetime(monkeypatch):
    """Patch datetime.now() to a fixed value."""
    fixed = datetime(2025, 1, 1)
    monkeypatch.setattr(reports_utils, "datetime", Mock(now=lambda: fixed))
    return fixed


@pytest.fixture
def fake_config(tmp_path, monkeypatch):
    """Patch load_config with a minimal config pointing to tmp_path."""
    config = {
        "business_name": "Test Store",
        "business_address": "123 Main St",
        "business_phone": "555-1234",
        "business_email": "test@test.com",
        "invoice_output_path": str(tmp_path),
    }
    monkeypatch.setattr(reports_utils, "load_config", lambda: config)
    return config


@pytest.fixture
def mock_pdf(monkeypatch):
    """Patch the PDF generator with a Mock."""
    mock = Mock()
    monkeypatch.setattr(
        reports_utils.generate_invoice, "generate_lottery_invoice_pdf", mock
    )
    return mock


@pytest.fixture
def mock_send_file(monkeypatch):
    """Patch send_file to return a sentinel response."""
    mock = Mock(return_value="SEND_FILE_RESPONSE")
    monkeypatch.setattr(reports_utils, "send_file", mock)
    return mock


# ============================================================
# create_daily_invoice tests
# ============================================================

def test_create_daily_invoice_invoice_log_error(monkeypatch):
    """A DB error on get_table_for_invoice returns an error tuple."""
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_table_for_invoice",
        lambda db, report_id: ("DB error", "error"),
    )

    monkeypatch.setattr(
        reports_utils,
        "check_error",
        lambda result, msg_data: msg_data.update(
            {"message": "err", "message_type": "error"}
        )
        or None,
    )

    result = reports_utils.create_daily_invoice("R1")

    assert result == ("ERROR: Unable to get the invoice table", "error")


def test_create_daily_invoice_daily_report_error(monkeypatch):
    """A DB error on get_daily_report returns an error tuple."""
    report_id = "R123"

    monkeypatch.setattr(
        "lottery_app.utils.reports.load_config",
        lambda: {
            "business_name": "Test Store",
            "business_address": "123 St",
            "business_phone": "123",
            "business_email": "test@test.com",
            "invoice_output_path": None,
        },
    )

    monkeypatch.setattr(
        "lottery_app.utils.reports.database_queries.get_table_for_invoice",
        lambda db_path, rid: [{"some": "data"}],
    )

    monkeypatch.setattr(
        "lottery_app.utils.reports.database_queries.get_daily_report",
        lambda db_path, rid: None,
    )

    def mock_check_error(result, msg_data, fallback=None):
        if result is None:
            msg_data["message"] = "error"
            msg_data["message_type"] = "error"
            return fallback
        return result

    monkeypatch.setattr("lottery_app.utils.reports.check_error", mock_check_error)

    result = reports_utils.create_daily_invoice(report_id)

    assert result == ("ERROR: Unable to create daily invoice", "error")


def test_create_daily_invoice_return_path_only(
    monkeypatch, fake_config, mock_pdf, fixed_datetime  # pylint: disable=unused-argument
):
    """Successful invoice creation with return_path_only=True returns the file path."""
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_table_for_invoice",
        lambda db, rid: [{"x": 1}],
    )
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_daily_report",
        lambda db, rid: {"total": 100},
    )
    monkeypatch.setattr(reports_utils, "check_error", lambda result, msg_data: result)

    path, status = reports_utils.create_daily_invoice("R1", return_path_only=True)

    assert status == "success"
    assert path.endswith("Invoice#R1-01-01-2025.pdf")
    mock_pdf.assert_called_once()


def test_create_daily_invoice_send_file(
    monkeypatch, fake_config, mock_pdf, mock_send_file, fixed_datetime  # pylint: disable=unused-argument
):
    """Successful invoice creation without return_path_only returns the send_file response."""
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_table_for_invoice",
        lambda db, rid: [{"x": 1}],
    )
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_daily_report",
        lambda db, rid: {"total": 100},
    )
    monkeypatch.setattr(reports_utils, "check_error", lambda result, msg_data: result)

    response, status = reports_utils.create_daily_invoice("R1")

    assert status == "success"
    assert response == "SEND_FILE_RESPONSE"
    mock_send_file.assert_called_once()


def test_create_daily_invoice_fallback_directory(
    monkeypatch, tmp_path, mock_pdf, fixed_datetime  # pylint: disable=unused-argument
):
    """An invalid output path falls back to ~/Downloads."""
    monkeypatch.setattr(
        reports_utils, "load_config", lambda: {"invoice_output_path": "/bad/path"}
    )

    monkeypatch.setattr(
        reports_utils.database_queries, "get_table_for_invoice", lambda *_: []
    )
    monkeypatch.setattr(
        reports_utils.database_queries, "get_daily_report", lambda *_: {}
    )
    monkeypatch.setattr(reports_utils, "check_error", lambda result, msg_data: result)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    path, _ = reports_utils.create_daily_invoice("R1", return_path_only=True)

    assert str(tmp_path / "Downloads") in path


def test_create_daily_invoice_generation_failure(monkeypatch, fake_config):  # pylint: disable=unused-argument
    """An OSError during PDF generation returns a 500 error tuple."""
    monkeypatch.setattr(
        reports_utils.database_queries, "get_table_for_invoice", lambda *_: []
    )
    monkeypatch.setattr(
        reports_utils.database_queries, "get_daily_report", lambda *_: {}
    )
    monkeypatch.setattr(reports_utils, "check_error", lambda result, msg_data: result)

    monkeypatch.setattr(
        reports_utils.generate_invoice,
        "generate_lottery_invoice_pdf",
        Mock(side_effect=OSError("disk full")),
    )

    result = reports_utils.create_daily_invoice("R1")

    assert result[1] == 500
    assert "Error generating invoice" in result[0]


# ============================================================
# add_sales_log helper stubs
# ============================================================


def success_check_error(result, message_holder=None, fallback=None, flash_prefix=None):  # pylint: disable=unused-argument
    """Stub that passes all results through unchanged."""
    return result


def error_check_error(message="DB error"):
    """Return a check_error stub that injects an error into message_holder."""
    def _inner(
        result_or_callable,  # pylint: disable=unused-argument
        message_holder=None,
        fallback=None,
        flash_prefix=None,  # pylint: disable=unused-argument
    ):
        if message_holder is not None:
            message_holder["message"] = message
            message_holder["message_type"] = "error"
        return fallback

    return _inner


# ============================================================
# add_sales_log tests
# ============================================================


def test_add_sales_log_success(monkeypatch):
    """Happy path: all DB calls succeed and the log is inserted correctly."""
    monkeypatch.setattr(reports_utils, "check_error", success_check_error)

    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_activated_book_is_at_ticketnumber",
        lambda db_path, book_id: 10,
    )

    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_ticket_name",
        lambda db_path, game_number: "Mega Bucks",
    )

    inserted = {}

    def mock_insert(_db_path, data):
        inserted.update(data)

    monkeypatch.setattr(reports_utils.update_sale_log, "insert_sales_log", mock_insert)

    msg, msg_type = reports_utils.add_sales_log(
        book_id="BOOK123", lastest_ticket_number=20, game_number="GAME999"
    )

    assert msg == ""
    assert msg_type == ""

    assert inserted == {
        "ActiveBookID": "BOOK123",
        "prev_TicketNum": 10,
        "current_TicketNum": 20,
        "Ticket_Name": "Mega Bucks",
        "Ticket_GameNumber": "GAME999",
    }


def test_add_sales_log_activated_book_error(monkeypatch):
    """A DB error fetching the activated book is propagated as an error tuple."""
    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_activated_book_is_at_ticketnumber",
        lambda *_: ("Activated book error", "error"),
    )

    monkeypatch.setattr(
        reports_utils.database_queries, "get_ticket_name", lambda *_: "Test Ticket"
    )

    monkeypatch.setattr(
        reports_utils.update_sale_log, "insert_sales_log", lambda *_: None
    )

    msg, msg_type = reports_utils.add_sales_log(
        book_id="BOOK1", lastest_ticket_number=10, game_number="GAME1"
    )

    assert msg == "Activated book error"
    assert msg_type == "error"


def test_add_sales_log_ticket_name_error(monkeypatch):
    """A DB error fetching the ticket name is propagated as an error tuple."""
    calls = {"count": 0}

    def selective_check_error(
        result, message_holder=None, fallback=None, flash_prefix=None  # pylint: disable=unused-argument
    ):
        calls["count"] += 1
        if calls["count"] == 2:
            message_holder["message"] = "Ticket name lookup failed"
            message_holder["message_type"] = "error"
            return fallback
        return result

    monkeypatch.setattr(reports_utils, "check_error", selective_check_error)

    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_activated_book_is_at_ticketnumber",
        lambda *_: 5,
    )

    monkeypatch.setattr(
        reports_utils.database_queries, "get_ticket_name", lambda *_: None
    )

    monkeypatch.setattr(
        reports_utils.update_sale_log, "insert_sales_log", lambda *_: None
    )

    msg, msg_type = reports_utils.add_sales_log("BOOK1", 10, "GAME1")

    assert msg == "Ticket name lookup failed"
    assert msg_type == "error"


def test_add_sales_log_insert_error(monkeypatch):
    """A DB error during insert is propagated as an error tuple."""
    def insert_error(
        result_or_callable,  # pylint: disable=unused-argument
        message_holder=None,
        fallback=None,
        flash_prefix=None,  # pylint: disable=unused-argument
    ):
        message_holder["message"] = "Insert failed"
        message_holder["message_type"] = "error"
        return fallback

    monkeypatch.setattr(
        reports_utils.database_queries,
        "get_activated_book_is_at_ticketnumber",
        lambda *_: 1,
    )

    monkeypatch.setattr(
        reports_utils.database_queries, "get_ticket_name", lambda *_: "Test Ticket"
    )

    monkeypatch.setattr(
        reports_utils.update_sale_log, "insert_sales_log", lambda *_: None
    )

    monkeypatch.setattr(reports_utils, "check_error", insert_error)

    msg, msg_type = reports_utils.add_sales_log("BOOK1", 2, "GAME1")

    assert msg == "Insert failed"
    assert msg_type == "error"


# ============================================================
# do_submit_procedure fixtures
# ============================================================


@pytest.fixture
def app():  # pylint: disable=redefined-outer-name
    """Return a minimal Flask app for request-context tests."""
    flask_app = Flask(__name__)
    flask_app.secret_key = "test"
    return flask_app


@pytest.fixture
def form_context(app):  # pylint: disable=redefined-outer-name
    """Provide a Flask request context pre-loaded with valid form data."""
    with app.test_request_context(
        method="POST",
        data={
            "instant_sold": "100",
            "online_sold": "50",
            "instant_cashed": "30",
            "online_cashed": "20",
            "cash_on_hand": "500",
        },
    ):
        yield


# ============================================================
# do_submit_procedure tests
# ============================================================


def test_do_submit_procedure_success(mocker, form_context):  # pylint: disable=unused-argument
    """All mocks succeed: the procedure returns a success message."""
    mock_check_error = mocker.patch("lottery_app.utils.reports.check_error")
    mock_db_queries = mocker.patch("lottery_app.utils.reports.database_queries")
    mock_update_sale_report = mocker.patch(
        "lottery_app.utils.reports.update_sale_report"
    )
    mock_update_sale_log = mocker.patch("lottery_app.utils.reports.update_sale_log")
    mock_update_ticket_timeline = mocker.patch(
        "lottery_app.utils.reports.update_ticket_timeline"
    )
    mock_update_activated_books = mocker.patch(
        "lottery_app.utils.reports.update_activated_books"
    )
    mock_email_invoice = mocker.patch("lottery_app.utils.reports.email_invoice")

    mock_check_error.side_effect = lambda result, *_: result

    mock_db_queries.next_report_id.return_value = 10
    mock_db_queries.get_all_sold_books.return_value = [
        {"BookID": 1},
        {"BookID": 2},
    ]

    message, message_type = do_submit_procedure()

    assert message == "SCANS SUBMITTED SUCCESSFULLY"
    assert message_type == "success"

    mock_update_sale_report.insert_daily_totals.assert_called_once()
    mock_update_sale_log.update_pending_sales_log_report_id.assert_called_once_with(
        ANY, 10
    )
    mock_update_ticket_timeline.update_pending_ticket_timeline_report_id.assert_called_once_with(
        ANY, 10
    )
    assert mock_update_activated_books.deactivate_book.call_count == 2
    mock_update_activated_books.update_is_at_ticketnumbers.assert_called_once()
    mock_update_activated_books.clear_counting_ticket_numbers.assert_called_once()
    mock_email_invoice.assert_called_once()


@patch("lottery_app.utils.reports.email_invoice")
@patch("lottery_app.utils.reports.database_queries.get_all_sold_books")
@patch("lottery_app.utils.reports.check_error")
def test_do_submit_procedure_check_error_failure(
    mock_check_error,
    mock_get_sold_books,
    mock_email_invoice,  # pylint: disable=unused-argument
    app,  # pylint: disable=redefined-outer-name
):
    """check_error injecting an error causes the procedure to return that error."""
    def check_error_side_effect(result, msg_data, *_args):
        msg_data["message"] = "DB ERROR"
        msg_data["message_type"] = "error"
        return result

    mock_check_error.side_effect = check_error_side_effect
    mock_get_sold_books.return_value = [{"BookID": 123}]

    with app.test_request_context(
        method="POST",
        data={
            "instant_sold": 10,
            "online_sold": 5,
            "instant_cashed": 2,
            "online_cashed": 1,
            "cash_on_hand": 100,
        },
    ):
        message, message_type = do_submit_procedure()

    assert message == "DB ERROR"
    assert message_type == "error"


@patch("lottery_app.utils.reports.database_queries")
@patch("lottery_app.utils.reports.check_error")
def test_do_submit_procedure_invalid_book_data(
    mock_check_error, mock_db_queries, form_context  # pylint: disable=unused-argument
):
    """A non-dict entry in get_all_sold_books returns an error tuple."""
    mock_check_error.side_effect = lambda result, *_: result
    mock_db_queries.next_report_id.return_value = 1
    mock_db_queries.get_all_sold_books.return_value = ["BAD_BOOK"]

    message, message_type = do_submit_procedure()

    assert message == "ERROR: Invalid book data"
    assert message_type == "error"


@patch("lottery_app.utils.reports.database_queries")
@patch("lottery_app.utils.reports.check_error")
def test_do_submit_procedure_value_error(
    mock_check_error, mock_db_queries, form_context  # pylint: disable=unused-argument
):
    """A ValueError from next_report_id is caught and returned as an error."""
    mock_db_queries.next_report_id.side_effect = ValueError("Invalid report id")

    message, message_type = do_submit_procedure()

    assert message == "Invalid report id"
    assert message_type == "error"


@patch("lottery_app.utils.reports.create_daily_invoice")
@patch("lottery_app.utils.reports.check_error")
def test_do_submit_procedure_file_not_found(
    mock_check_error, mock_create_invoice, form_context  # pylint: disable=unused-argument
):
    """A FileNotFoundError during invoice creation returns an 'Invoice not found' error."""
    mock_check_error.side_effect = lambda result, *_: result
    mock_create_invoice.side_effect = FileNotFoundError("invoice.pdf")

    message, message_type = do_submit_procedure()

    assert "Invoice not found" in message
    assert message_type == "error"


@patch("lottery_app.utils.reports.database_queries")
@patch("lottery_app.utils.reports.check_error")
def test_do_submit_procedure_unexpected_exception(
    mock_check_error, mock_db_queries, form_context  # pylint: disable=unused-argument
):
    """An unexpected TypeError is caught and returned as an error with 'Unexpected error:'."""
    mock_check_error.side_effect = lambda result, *_: result
    mock_db_queries.next_report_id.side_effect = TypeError("Boom")

    message, message_type = do_submit_procedure()

    assert message.startswith("Unexpected error:")
    assert message_type == "error"


@patch("lottery_app.utils.reports.database_queries")
@patch("lottery_app.utils.reports.update_activated_books")
@patch("lottery_app.utils.reports.check_error")
def test_do_submit_procedure_no_sold_books(
    mock_check_error,
    mock_update_activated_books,
    mock_db_queries,
    form_context,  # pylint: disable=unused-argument
):
    """When there are no sold books the procedure still returns success."""
    mock_check_error.side_effect = lambda result, *_: result
    mock_db_queries.next_report_id.return_value = 5
    mock_db_queries.get_all_sold_books.return_value = []

    message, message_type = do_submit_procedure()

    assert message == "SCANS SUBMITTED SUCCESSFULLY"
    assert message_type == "success"
    mock_update_activated_books.deactivate_book.assert_not_called()
