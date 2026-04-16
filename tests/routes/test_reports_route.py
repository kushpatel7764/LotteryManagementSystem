"""Tests for the reports route: helper functions and HTTP endpoints."""
import json
from urllib.parse import parse_qs, urlparse

from unittest.mock import MagicMock

import pytest

from lottery_app.routes.reports import (
    _create_scan_id,
    _get_latest_report_id,
    _get_book_metadata,
)

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def admin_user(mocker):
    """Return a mocked admin User and patch User.get_by_id."""
    user = MagicMock()
    user.id = 1
    user.role = "admin"
    mocker.patch("lottery_app.routes.reports.User.get_by_id", return_value=user)
    return user


@pytest.fixture
def normal_user(mocker):
    """Return a mocked standard User and patch User.get_by_id."""
    user = MagicMock()
    user.id = 2
    user.role = "user"
    mocker.patch("lottery_app.routes.reports.User.get_by_id", return_value=user)
    return user


@pytest.fixture
def login_admin(client, admin_user):  # pylint: disable=redefined-outer-name
    """Inject an admin session into the test client."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_user.id)
    return client


@pytest.fixture
def login_user(client, normal_user):  # pylint: disable=redefined-outer-name
    """Inject a standard-user session into the test client."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(normal_user.id)
    return client


# ------------------------------------------------------------------
# Helper Function Tests
# ------------------------------------------------------------------


def test_create_scan_id():
    """_create_scan_id concatenates all parts in the correct order."""
    scan_id = _create_scan_id(
        game_number="123",
        book_id="B1",
        ticket_num="10",
        ticket_price="5",
        book_amount="100",
    )
    assert scan_id == "123B1105100"


def test_get_latest_report_id_success(mocker):
    """_get_latest_report_id returns next_report_id minus one on success."""
    mocker.patch(
        "lottery_app.routes.reports.database_queries.next_report_id",
        return_value=10,
    )

    msg_data = {}
    latest = _get_latest_report_id(msg_data)
    assert latest == 9


def test_get_latest_report_id_error(mocker):
    """_get_latest_report_id returns 0 when the database raises."""
    mocker.patch(
        "lottery_app.routes.reports.database_queries.next_report_id",
        side_effect=Exception("DB fail"),
    )

    msg_data = {}
    latest = _get_latest_report_id(msg_data)

    assert latest == 0


def test_get_book_metadata_success(mocker):
    """_get_book_metadata returns game number, book tuple, and ticket name."""
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_game_num_of",
        return_value="123",
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_book",
        return_value=("id", "x", "y", 100, 5),
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_ticket_name",
        return_value="Mega Bucks",
    )

    msg_data = {}
    game, book, name = _get_book_metadata("B1", msg_data)

    assert game == "123"
    assert name == "Mega Bucks"
    assert book[3] == 100


# ------------------------------------------------------------------
# /edit_reports
# ------------------------------------------------------------------


def test_edit_reports_success(client, auth, mocker):
    """GET /edit_reports renders the page with report data."""
    auth.login()
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_all_sales_reports",
        return_value=[{"ReportDate": "2024-01-01", "ReportTime": "12:00:00"}],
    )
    mocker.patch(
        "lottery_app.routes.reports.convert_utc_to_local", side_effect=lambda dt, tz: dt
    )

    resp = client.get("/edit_reports")

    assert resp.status_code == 200
    assert b"Edit Reports" in resp.data
    assert b"Filtered Results" in resp.data
    assert b"2024-01-01" in resp.data
    assert b"12:00 PM" in resp.data


def test_edit_reports_invalid_report_format(  # pylint: disable=redefined-outer-name
    client, login_admin, mocker  # pylint: disable=unused-argument
):
    """GET /edit_reports handles malformed report rows gracefully."""
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_all_sales_reports",
        return_value=["bad-data"],
    )

    resp = client.get("/edit_reports")
    assert resp.status_code == 200


# ------------------------------------------------------------------
# /edit_report/<id>
# ------------------------------------------------------------------


def test_edit_single_report_admin_access(  # pylint: disable=redefined-outer-name
    client, login_admin, mocker  # pylint: disable=unused-argument
):
    """Admin can GET /edit_report/<id> and receives the edit template."""
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_sales_log", return_value=[]
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_daily_report",
        return_value={"InstantTicketSold": 0},
    )
    mocker.patch(
        "lottery_app.routes.reports.calculate_instant_tickets_sold", return_value=5
    )
    mocker.patch(
        "lottery_app.routes.reports.load_config",
        return_value={"ticket_order": "ascending"},
    )

    resp = client.get("/edit_report/1")
    assert resp.status_code == 200
    assert b"edit_single_report" in resp.data


def test_edit_single_report_non_admin_redirect(  # pylint: disable=redefined-outer-name
    client, login_user  # pylint: disable=unused-argument
):
    """Non-admin users are redirected away from /edit_report/<id>."""
    resp = client.get("/edit_report/1", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Unauthorized access" in resp.data


# ------------------------------------------------------------------
# /update_salesLog
# ------------------------------------------------------------------


def test_update_sales_log_success(  # pylint: disable=redefined-outer-name
    client, login_admin, mocker  # pylint: disable=unused-argument
):
    """Valid POST to /update_salesLog returns a redirect URL."""
    mocker.patch(
        "lottery_app.routes.reports.database_queries.is_sold", return_value=False
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_game_num_of",
        return_value="123",
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_book",
        return_value=("id", "x", "y", 100, 5),
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_ticket_name",
        return_value="Mega",
    )
    mocker.patch(
        "lottery_app.routes.reports.calculate_instant_tickets_sold", return_value=10
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.next_report_id", return_value=5
    )
    mocker.patch(
        "lottery_app.routes.reports.load_config",
        return_value={"ticket_order": "ascending"},
    )

    payload = {
        "bookID": "B1",
        "reportID": "3",
        "open": "10",
        "close": "20",
    }

    resp = client.post(
        "/update_salesLog",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert resp.status_code == 200
    data = resp.get_json()
    assert "redirect_url" in data


def test_update_sales_log_ticket_exceeds_book(  # pylint: disable=redefined-outer-name
    client, login_admin, mocker  # pylint: disable=unused-argument
):
    """Ticket number exceeding book amount returns an error redirect URL."""
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_book",
        return_value=("id", "x", "y", 20, 5),
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.get_game_num_of",
        return_value="123",
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.is_sold", return_value=False
    )
    mocker.patch(
        "lottery_app.routes.reports.database_queries.next_report_id", return_value=3
    )

    resp = client.post(
        "/update_salesLog",
        json={
            "bookID": "B1",
            "reportID": "1",
            "open": "10",
            "close": "30",
        },
    )

    data = resp.get_json()

    parsed = urlparse(data["redirect_url"])
    qs = parse_qs(parsed.query)

    assert qs["message"][0] == "Ticket number cannot exceed or equal book amount."
    assert qs["message_type"][0] == "error"


# ------------------------------------------------------------------
# /update_sale_report
# ------------------------------------------------------------------


def test_update_sale_report_success(  # pylint: disable=redefined-outer-name
    client, login_admin, mocker  # pylint: disable=unused-argument
):
    """Valid POST to /update_sale_report/<id> returns 200."""
    mocker.patch(
        "lottery_app.routes.reports.update_sale_report.update_sale_report",
        return_value=("OK", "success"),
    )

    resp = client.post(
        "/update_sale_report/1",
        data={
            "instant_sold": "10",
            "online_sold": "2",
            "instant_cashed": "3",
            "online_cashed": "1",
            "cash_on_hand": "100",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200


# ------------------------------------------------------------------
# /download/<id>
# ------------------------------------------------------------------


def test_download_report_success(  # pylint: disable=redefined-outer-name
    client, login_admin, mocker  # pylint: disable=unused-argument
):
    """GET /download/<id> returns the PDF bytes on success."""
    # Route does `return result[0]`; wrapping in a 1-tuple lets check_error pass
    # it through unchanged so result[0] becomes the response body.
    mocker.patch(
        "lottery_app.routes.reports.create_daily_invoice", return_value=("PDF_BYTES",)
    )

    resp = client.get("/download/1")
    assert resp.status_code == 200
    assert resp.data == b"PDF_BYTES"


def test_download_report_error(  # pylint: disable=redefined-outer-name
    client, login_admin, mocker  # pylint: disable=unused-argument
):
    """GET /download/<id> returns 500 when invoice generation raises."""
    mocker.patch(
        "lottery_app.routes.reports.create_daily_invoice", side_effect=Exception("fail")
    )

    resp = client.get("/download/1")
    assert resp.status_code == 500
    assert b"fail" in resp.data
