import pytest
from unittest.mock import patch, MagicMock

from lottery_app.utils.config import load_config
from lottery_app.routes.tickets import tickets_bp


# -----------------------------
# Helpers
# -----------------------------

def post_scan(client, barcode="123456"):
    return client.post(
        "/scan_tickets",
        data={"scanned_code": barcode},
        follow_redirects=True
    )


# -----------------------------
# /scan_tickets
# -----------------------------
@patch("lottery_app.routes.tickets.flash")
@patch("lottery_app.database.database_queries.get_all_active_book_ids")
@patch("lottery_app.routes.tickets.ScannedCodeManagement")
def test_scan_invalid_barcode(mock_scan_mgr, mock_active_ids, mock_flash, client, auth):
    auth.login()
    
    mock_active_ids.return_value = ["B1"]
    mock_scan_mgr.return_value.extract_all_scanned_code.return_value = "INVALID BARCODE"
    
    resp = client.post(
        "/scan_tickets",
        data={"scanned_code": "123456"},
        follow_redirects=False
    )

    assert resp.status_code == 200

    mock_flash.assert_any_call("INVALID BARCODE", "tickets_error")

@patch("lottery_app.routes.tickets.flash")
@patch("lottery_app.database.database_queries.get_all_active_book_ids")
@patch("lottery_app.routes.tickets.ScannedCodeManagement")
def test_scan_book_not_activated(mock_scan_mgr, mock_active_ids, mock_flash, client, auth):
    auth.login()
    mock_active_ids.return_value = ["B1"]

    mock_scan_mgr.return_value.extract_all_scanned_code.return_value = {
        "book_id": "B2",
        "game_number": "123",
        "ticket_number": 1,
        "ticket_price": 5,
    }

    resp = post_scan(client)
    assert resp.status_code == 200
    
    mock_flash.assert_any_call("Book IS NOT ACTIVATED! PLEASE ACTIVATE BEFORE SCANNING.", "tickets_error")

@patch("lottery_app.routes.tickets.flash")
@patch("lottery_app.routes.tickets.insert_ticket")
@patch("lottery_app.routes.tickets.add_sales_log")
@patch("lottery_app.routes.tickets.update_activated_books.update_counting_ticket_number")
@patch("lottery_app.routes.tickets.database_queries.get_ticket_name")
@patch("lottery_app.database.database_queries.is_counting_ticket_number_set")
@patch("lottery_app.database.database_queries.get_all_active_book_ids")
@patch("lottery_app.routes.tickets.ScannedCodeManagement")
def test_scan_ticket_success(
    mock_scan_mgr,
    mock_active_ids,
    mock_is_set,
    mock_ticket_name,
    mock_update_count,
    mock_add_sales,
    mock_insert_ticket,
    mock_flash,
    client,
    auth
):
    auth.login()
    mock_active_ids.return_value = ["B1"]
    mock_is_set.return_value = False
    mock_ticket_name.return_value = "Lucky 7"

    mock_scan_mgr.return_value.extract_all_scanned_code.return_value = {
        "book_id": "B1",
        "game_number": "123",
        "ticket_number": 10,
        "ticket_price": 5,
    }

    resp = post_scan(client)
    assert resp.status_code == 200

    mock_flash.assert_any_call("TICKET SCANNED", "tickets_success")
    mock_insert_ticket.assert_called_once()
    mock_add_sales.assert_called_once()
    mock_update_count.assert_called_once()

@patch("lottery_app.routes.tickets.flash")
@patch("lottery_app.database.database_queries.is_counting_ticket_number_set")
@patch("lottery_app.database.database_queries.get_all_active_book_ids")
@patch("lottery_app.routes.tickets.ScannedCodeManagement")
def test_scan_duplicate_ticket(mock_scan_mgr, mock_active_ids, mock_is_set, mock_flash, client, auth):
    auth.login()
    mock_active_ids.return_value = ["B1"]
    mock_is_set.return_value = True

    mock_scan_mgr.return_value.extract_all_scanned_code.return_value = {
        "book_id": "B1",
        "game_number": "123",
        "ticket_number": 10,
        "ticket_price": 5,
    }

    resp = post_scan(client)
    assert resp.status_code == 200

    mock_flash.assert_any_call("""A ticket from this book has already been scanned.
                    Please use the UNDO button if you want to rescan.""".upper(), "tickets_error")


# -----------------------------
# /undo_scan
# -----------------------------
@patch("lottery_app.routes.tickets.flash")
@patch("lottery_app.routes.tickets.update_books.update_is_sold_for_book")
@patch("lottery_app.routes.tickets.update_activated_books.clear_counting_ticket_number")
@patch("lottery_app.routes.tickets.update_sale_log.delete_sales_log_by_book_id")
@patch("lottery_app.routes.tickets.update_ticket_timeline.delete_ticket_timeline_by_book_id")
def test_undo_scan_success(
    mock_delete_timeline,
    mock_delete_sales,
    mock_clear_count,
    mock_mark_unsold,
    mock_flash,
    client,
    auth
):
    auth.login()
    resp = client.post(
        "/undo_scan",
        data={"book_id": "B1"},
        follow_redirects=True
    )
    assert resp.status_code == 200

    mock_flash.assert_any_call("UNDONE SUCCESSFUL", "tickets_success")
    mock_delete_timeline.assert_called_once()
    mock_delete_sales.assert_called_once()
    mock_clear_count.assert_called_once()
    mock_mark_unsold.assert_called_once()

@patch("lottery_app.routes.tickets.flash")
@patch("lottery_app.routes.tickets.update_ticket_timeline.delete_ticket_timeline_by_book_id")
def test_undo_scan_error(mock_delete, mock_flash, client, auth):
    auth.login()
    mock_delete.side_effect = Exception("boom")

    resp = client.post(
        "/undo_scan",
        data={"book_id": "B1"},
        follow_redirects=True
    )
    assert resp.status_code == 200
    mock_flash.assert_any_call("Unexpected error: boom", "tickets_error")


# -----------------------------
# /book_sold_out
# -----------------------------

@patch("lottery_app.routes.tickets.insert_ticket")
@patch("lottery_app.routes.tickets.add_sales_log")
@patch("lottery_app.database.database_queries.get_ticket_name")
@patch("lottery_app.database.database_queries.get_book")
@patch("lottery_app.routes.tickets.update_activated_books.update_counting_ticket_number")
@patch("lottery_app.routes.tickets.update_books.update_is_sold_for_book")
def test_book_sold_out_success(
    mock_mark_sold,
    mock_update_count,
    mock_get_book,
    mock_ticket_name,
    mock_add_sales,
    mock_insert_ticket,
    client, 
    auth,
    monkeypatch
):
    auth.login()
    monkeypatch.setattr(
        "lottery_app.utils.config.load_config",
        lambda: {"ticket_order": "ascending"}
    )

    mock_get_book.return_value = ("B1", "123", None, 100, 5)
    mock_ticket_name.return_value = "Lucky 7"

    resp = client.post(
        "/book_sold_out",
        data={"book_id": "B1"},
        follow_redirects=True
    )

    assert b"BOOK MARKED AS SOLD OUT" in resp.data
    mock_mark_sold.assert_called_once()
    mock_update_count.assert_called_once()
    mock_insert_ticket.assert_called_once()
    mock_add_sales.assert_called_once()


def test_book_sold_out_no_book_id(client, auth):
    auth.login()
    resp = client.post(
        "/book_sold_out",
        data={},
        follow_redirects=True
    )

    assert b"No Book ID provided" in resp.data


# -----------------------------
# /submit
# -----------------------------

@patch("lottery_app.routes.tickets.do_submit_procedure")
@patch("lottery_app.database.database_queries.can_submit")
def test_submit_success(mock_can_submit, mock_submit, client, auth):
    auth.login()
    mock_can_submit.return_value = True
    mock_submit.return_value = None

    resp = client.post("/submit", follow_redirects=True)

    assert resp.status_code == 200


@patch("lottery_app.routes.tickets.database_queries.can_submit")
def test_submit_blocked(mock_can_submit, client, auth):
    auth.login()
    mock_can_submit.return_value = False

    resp = client.post("/submit", follow_redirects=True)

    assert resp.status_code == 200


@patch("lottery_app.routes.tickets.do_submit_procedure")
@patch("lottery_app.database.database_queries.can_submit")
def test_submit_error(mock_can_submit, mock_submit, client, auth):
    auth.login()
    mock_can_submit.return_value = True
    mock_submit.return_value = ("ERROR", "error")

    resp = client.post("/submit", follow_redirects=True)

    assert b"ERROR" in resp.data
