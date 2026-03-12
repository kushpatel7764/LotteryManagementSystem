import pytest
from unittest.mock import MagicMock

from lottery_app.utils.books import (
    activate_book_procedure,
    add_book_procedure,
)

#------------------------------------------------------------------------------
# Pytest: test suite for books management functions in lottery_app.utils.books
#------------------------------------------------------------------------------
"""
Testing Code: 35600949981000515070000000091
activate_book_procedure:
✔ invalid barcode
✔ book does not exist
✔ already activated
✔ previous activation restores ticket number
✔ normal activation success path
✔ unexpected exception handling
✔ correct propagation of check_error messages
add_book_procedure:
✔ invalid barcode
✔ lookup table update fails → still inserts book, returns warning
✔ lookup table success → successful insertion
✔ book insertion error
✔ combines messages correctly
"""
# ============================================================
# activate_book_procedure tests
# ============================================================

@pytest.fixture
def scanned_info_mock(mocker):
    """Patch ScannedCodeManagement constructor and return its instance mock."""
    obj = MagicMock()
    mocker.patch(
        "lottery_app.scanned_code_information_management",
        return_value=obj
    )
    return obj

def test_activate_book_invalid_barcode(scanned_info_mock):
    scanned_info_mock.extract_all_scanned_code.return_value = "INVALID BARCODE"

    result = activate_book_procedure("ANY")
    assert result == ("INVALID BARCODE", "error")

def test_activate_book_book_not_exists(scanned_info_mock, mocker):
    scanned_info_mock.extract_all_scanned_code.return_value = {
        "book_id": "094998",
        "ticket_number": "100",
        "game_number": "356",
        "book_amount": "149",
        "ticket_price": "5",
    }

    mocker.patch(
        "lottery_app.database.database_queries.is_book",
        return_value=False
    )
    mocker.patch(
        "lottery_app.database.database_queries.is_activated_book",
        return_value=False
    )

    msg, msg_type = activate_book_procedure("35600949981000515070000000091")
    assert msg == "BOOK DOES NOT EXISTS IN BOOKS DATABASE!"
    assert msg_type == "error"


def test_activate_book_already_activated(scanned_info_mock, mocker):
    scanned_info_mock.extract_all_scanned_code.return_value = {
        "book_id": "094998",
        "ticket_number": "11",
        "game_number": "356",
        "book_amount": "149",
        "ticket_price": "5",
    }

    mocker.patch(
        "lottery_app.database.database_queries.is_book",
        return_value=True
    )
    mocker.patch(
        "lottery_app.database.database_queries.is_activated_book",
        return_value=True
    )

    msg, msg_type = activate_book_procedure("35600949981000515070000000091")
    assert msg == "BOOK HAS ALREADY BEEN ACTIVATED!"
    assert msg_type == "error"


def test_activate_book_previous_activation_sets_ticket_number(mocker, scanned_info_mock):
    scanned_info_mock.extract_all_scanned_code.return_value = {
        "book_id": "094995",
        "ticket_number": "011",
        "game_number": "356",
        "book_amount": "149",
        "ticket_price": "5",
    }

    mocker.patch("lottery_app.database.database_queries.is_book", return_value=True)
    mocker.patch("lottery_app.database.database_queries.is_activated_book", return_value=False)

    # was_activated returns an earlier ticket index
    mocker.patch(
        "lottery_app.database.database_queries.was_activated",
        return_value=5
    )

    # make check_error write to msg_data
    def fake_check_error(*args, **kwargs):
        message_holder = kwargs.get("message_holder") or args[1]
        message_holder["message"] = "ACTIVATION SUCCESS"
        message_holder["message_type"] = "success"
        

    mocker.patch("lottery_app.utils.books.check_error", side_effect=fake_check_error)

    insert_mock = mocker.patch(
        "lottery_app.database.update_activated_books.insert_book_to_activated_book_table",
        return_value=True,
    )
    msg, msg_type = activate_book_procedure("35600949980110515070000000091")
    assert msg == "ACTIVATION SUCCESS"
    assert msg_type == "success"
    
    # ---- CRITICAL ASSERTIONS ----
    # Ensure the mock was actually called
    insert_mock.assert_called_once()

    # Extract the activation info passed to DB insert
    called_args = insert_mock.call_args[1]  # keyword arguments

    active_book_info = called_args["active_book_info"]

    # Assert the previous activation ticket number overwrote the scanned one
    assert active_book_info["isAtTicketNumber"] == "011"

    # Quick sanity checks
    assert active_book_info["ActiveBookID"] == "094998"
    assert active_book_info["ActivationID"] == "35600949980110515070000000091"


def test_activate_book_no_previous_activation(mocker, scanned_info_mock):
    from lottery_app.utils.books import db_path
    scanned_info_mock.extract_all_scanned_code.return_value = {
        "book_id": "094998",
        "ticket_number": "99",
        "game_number": "356",
        "book_amount": "149",
        "ticket_price": "5",
    }
    
    # Patch db_path used inside the function
    mocker.patch("lottery_app.database.database_queries.is_book", return_value=True)
    mocker.patch("lottery_app.database.database_queries.is_activated_book", return_value=False)
    # No previous activation
    was_activated_mock = mocker.patch("lottery_app.database.database_queries.was_activated", return_value=None)
    # make check_error write to msg_data
    def fake_check_error(*args, **kwargs):
        message_holder = kwargs.get("message_holder") or args[1]
        message_holder["message"] = "ADDED SUCCESSFULLY"
        message_holder["message_type"] = "success"

    mocker.patch("lottery_app.utils.books.check_error", side_effect=fake_check_error)
    insert_mock = mocker.patch(
        "lottery_app.database.update_activated_books.insert_book_to_activated_book_table",
        return_value=True,
    )

    msg, msg_type = activate_book_procedure("35600949981000515070000000091")
    assert msg == "ADDED SUCCESSFULLY"
    assert msg_type == "success"
    
    # ---- REAL VERIFICATION ----
    # Ensure we actually checked for previous activation
    was_activated_mock.assert_called_once_with(db_path, "094998")

    # Verify insert call happened
    insert_mock.assert_called_once()

    # Extract activation data
    active_book_info = insert_mock.call_args[1]["active_book_info"]

    # The ticket number must stay as scanned (99)
    assert active_book_info["isAtTicketNumber"] == "100"

    # Sanity checks
    assert active_book_info["ActiveBookID"] == "094998"
    assert active_book_info["ActivationID"] == "35600949981000515070000000091"


def test_activate_book_unexpected_exception(mocker, scanned_info_mock):
    mocker.patch(
        "lottery_app.database.database_queries.is_book",
        side_effect=Exception("DB Failure")
    )

    scanned_info_mock.extract_all_scanned_code.return_value = {
        "book_id": "094998",
        "ticket_number": "99",
        "game_number": "356",
        "book_amount": "149",
        "ticket_price": "5",
    }

    msg, msg_type = activate_book_procedure("35600949981000515070000000091")
    assert msg.startswith("Unexpected Error: DB Failure")
    assert msg_type == "error"


# ============================================================
# add_book_procedure tests
# ============================================================

@pytest.fixture
def scan_info_add_mock(mocker):
    obj = MagicMock()
    mocker.patch(
        "lottery_app.scanned_code_information_management",
        return_value=obj
    )
    return obj


def test_add_book_invalid_barcode(scan_info_add_mock):
    # Book: 356-094998-100
    scan_info_add_mock.extract_all_scanned_code.return_value = "INVALID BARCODE"

    result = add_book_procedure("ANY")
    assert result == ("INVALID BARCODE", "error")


def test_add_book_lookup_insert_error(scan_info_add_mock, mocker):
    # Book: 356-094998-100
    scan_info_add_mock.extract_all_scanned_code.return_value = {
        "book_id": "094998",
        "game_number": "100",
        "book_amount": "149",
        "ticket_price": "05",
    }

    mocker.patch(
        "lottery_app.game_number_lookup_table.insert_new_ticket_name_to_lookup_table",
        return_value=("lookup failed", "error")
    )

    mocker.patch(
        "lottery_app.database.update_books.insert_book_info_to_books_table",
        return_value=("added", "success"),
    )

    msg, msg_type = add_book_procedure("35600949981000515070000000091")
    assert "Book added, but TicketName update failed" in msg
    assert msg_type == "warning"


def test_add_book_lookup_success(mocker, scan_info_add_mock):
    # Book info to be returned by the mock
    scan_info_add_mock.extract_all_scanned_code.return_value = {
        "book_id": "094998",
        "game_number": "100",
        "book_amount": "149",
        "ticket_price": "05",
    }
    

    mocker.patch(
        "lottery_app.game_number_lookup_table.insert_new_ticket_name_to_lookup_table",
        return_value=("lookup ok", "success")
    )

    mocker.patch(
        "lottery_app.database.update_books.insert_book_info_to_books_table",
        return_value=("BOOK ADDED", "success"),
    )

    msg, msg_type = add_book_procedure("35600949981000515070000000091")
    assert msg == "BOOK ADDED"
    assert msg_type == "success"


def test_add_book_insert_error(mocker, scan_info_add_mock):
    scan_info_add_mock.extract_all_scanned_code.return_value = {
        "book_id": "094998",
        "game_number": "100",
        "book_amount": "149",
        "ticket_price": "05",
    }

    mocker.patch(
        "lottery_app.game_number_lookup_table.insert_new_ticket_name_to_lookup_table",
        return_value=("lookup ok", "success")
    )

    mocker.patch(
        "lottery_app.database.update_books.insert_book_info_to_books_table",
        return_value=("DB ERROR", "error"),
    )

    msg, msg_type = add_book_procedure("35600949981000515070000000091")
    assert msg == "DB ERROR"
    assert msg_type == "error"