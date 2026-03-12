import pytest
from unittest.mock import patch, MagicMock

from lottery_app.utils.tickets import insert_ticket


# ---------- Helpers ----------

def success_check_error(return_value, message_holder):
    message_holder["message"] = "SUCCESS"
    message_holder["message_type"] = "success"
    return return_value


def error_check_error(return_value, message_holder):
    message_holder["message"] = "DB ERROR"
    message_holder["message_type"] = "error"
    return return_value


# ---------- Tests ----------

@patch("lottery_app.utils.tickets.update_ticket_timeline.insert_ticket_to_ticket_timeline_table")
@patch("lottery_app.utils.tickets.check_error")
def test_insert_ticket_success_without_report_id(
    mock_check_error,
    mock_insert_ticket,
):
    mock_insert_ticket.return_value = None
    mock_check_error.side_effect = success_check_error

    message, message_type = insert_ticket(
        scan_id="SCAN123",
        book_id="BOOK1",
        ticket_number=10,
        ticket_name="Mega Bucks",
        ticket_price=5.0,
    )

    assert message == "SUCCESS"
    assert message_type == "success"

    mock_insert_ticket.assert_called_once()
    args, _ = mock_insert_ticket.call_args

    # db_path is first arg, ticket_info second
    ticket_info = args[1]

    assert ticket_info == {
        "ScanID": "SCAN123",
        "BookID": "BOOK1",
        "TicketNumber": 10,
        "TicketName": "Mega Bucks",
        "TicketPrice": 5.0,
    }


@patch("lottery_app.utils.tickets.update_ticket_timeline.insert_ticket_to_ticket_timeline_table")
@patch("lottery_app.utils.tickets.check_error")
def test_insert_ticket_success_with_report_id(
    mock_check_error,
    mock_insert_ticket,
):
    mock_insert_ticket.return_value = None
    mock_check_error.side_effect = success_check_error

    message, message_type = insert_ticket(
        scan_id="SCAN456",
        book_id="BOOK2",
        ticket_number=25,
        ticket_name="Lucky 7",
        ticket_price=2.0,
        report_id="REPORT99",
    )

    assert message == "SUCCESS"
    assert message_type == "success"

    args, _ = mock_insert_ticket.call_args
    ticket_info = args[1]

    assert ticket_info["ReportID"] == "REPORT99"


@patch("lottery_app.utils.tickets.update_ticket_timeline.insert_ticket_to_ticket_timeline_table")
@patch("lottery_app.utils.tickets.check_error")
def test_insert_ticket_db_error(
    mock_check_error,
    mock_insert_ticket,
):
    mock_insert_ticket.return_value = None
    mock_check_error.side_effect = error_check_error

    message, message_type = insert_ticket(
        scan_id="SCAN999",
        book_id="BOOKX",
        ticket_number=1,
        ticket_name="Fail Ticket",
        ticket_price=1.0,
    )

    assert message == "DB ERROR"
    assert message_type == "error"


@patch("lottery_app.utils.tickets.update_ticket_timeline.insert_ticket_to_ticket_timeline_table")
@patch("lottery_app.utils.tickets.check_error")
def test_insert_ticket_calls_check_error_with_message_holder(
    mock_check_error,
    mock_insert_ticket,
):
    mock_insert_ticket.return_value = None

    insert_ticket(
        scan_id="SCAN777",
        book_id="BOOK7",
        ticket_number=7,
        ticket_name="Test Ticket",
        ticket_price=7.0,
    )

    # Ensure check_error is called with message_holder kwarg
    _, kwargs = mock_check_error.call_args
    assert "message_holder" in kwargs
    assert kwargs["message_holder"] == {"message": "", "message_type": ""}
