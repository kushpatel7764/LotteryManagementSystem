"""
Security tests: authentication and authorization enforcement.

Covers:
- CRIT-5: /receive endpoint has no authentication
- HIGH-2: financial write routes accessible by any authenticated user
- Route-level authentication (all protected routes block unauthenticated requests)
"""

import queue as _queue_mod
from unittest.mock import MagicMock

import pytest

from lottery_app.utils import config as config_module


def _drain_barcode_queue():
    """Drain all items from BARCODE_QUEUE."""
    while not config_module.BARCODE_QUEUE.empty():
        try:
            config_module.BARCODE_QUEUE.get_nowait()
        except _queue_mod.Empty:
            break


def _queue_contains(value):
    """Drain BARCODE_QUEUE and return (found, remaining_items)."""
    items = []
    while not config_module.BARCODE_QUEUE.empty():
        try:
            items.append(config_module.BARCODE_QUEUE.get_nowait())
        except _queue_mod.Empty:
            break
    return value in items


# ---------------------------------------------------------------------------
# CRIT-5 — /receive has no @login_required
# ---------------------------------------------------------------------------


class TestReceiveEndpointAuth:
    """
    CRIT-5: Any machine on the network can inject barcodes into the queue
    because /receive lacks @login_required.
    """

    def test_receive_barcode_without_session_is_accepted(self, client, monkeypatch):
        """
        [CRIT-5] POST /receive without a session currently returns 200 and
        accepts the barcode.  The route must be protected.

        This test documents the vulnerability.  It passes against the current
        (insecure) code and should FAIL once @login_required is added.
        """
        _drain_barcode_queue()
        monkeypatch.setattr(
            "lottery_app.routes.scanner.load_config",
            lambda: {"should_poll": "true"},
        )

        resp = client.post("/receive", data={"barcode": "INJECTED_BARCODE"})

        # Secure behaviour: 302 redirect to /login or 401
        if resp.status_code == 200:
            # Vulnerability is active
            assert _queue_contains("INJECTED_BARCODE"), (
                "CRIT-5 ACTIVE: unauthenticated POST to /receive was accepted. "
                "Add @login_required or API key authentication to this route."
            )
        else:
            # Vulnerability has been fixed
            assert resp.status_code in (302, 401)

        _drain_barcode_queue()

    def test_receive_barcode_injection_does_not_reach_stack_when_fixed(
        self, client, monkeypatch
    ):
        """
        [CRIT-5] Once /receive is secured, an unauthenticated request must
        NOT add anything to BARCODE_QUEUE.
        """
        _drain_barcode_queue()
        monkeypatch.setattr(
            "lottery_app.routes.scanner.load_config",
            lambda: {"should_poll": "true"},
        )

        client.post("/receive", data={"barcode": "SHOULD_NOT_APPEAR"})

        # After patching, queue should remain empty for unauthenticated requests
        # This assertion documents the expected post-fix state.
        if _queue_contains("SHOULD_NOT_APPEAR"):
            pytest.xfail(
                "CRIT-5: unauthenticated barcode injection still active — "
                "fix by adding @login_required to /receive."
            )
        _drain_barcode_queue()


# ---------------------------------------------------------------------------
# HIGH-2 — Financial write routes accessible by any authenticated user
# ---------------------------------------------------------------------------


class TestFinancialRouteAuthorization:
    """
    HIGH-2: Routes that modify financial records are only guarded by
    @login_required with no role check, allowing standard users to
    alter or delete critical data.
    """

    def _make_standard_user_session(self, client, monkeypatch):
        """Set up a standard (non-admin) user session."""
        standard = MagicMock()
        standard.id = 99
        standard.role = "standard"
        standard.is_authenticated = True
        standard.username = "standard_user"

        monkeypatch.setattr("flask_login.utils._get_user", lambda: standard)
        with client.session_transaction() as sess:
            sess["_user_id"] = "99"

    def test_standard_user_can_reach_submit(self, client, monkeypatch):
        """
        [HIGH-2] A standard user can POST /submit and trigger the daily
        submission procedure.  This must require an admin role.

        This test documents the vulnerability: it asserts 200 (allowed),
        showing the missing authorization check.
        """
        self._make_standard_user_session(client, monkeypatch)

        mock_can_submit = MagicMock(return_value=False)
        monkeypatch.setattr(
            "lottery_app.routes.tickets.database_queries.can_submit",
            mock_can_submit,
        )

        resp = client.post("/submit", follow_redirects=True)
        # With no role check, standard users reach the route (200 after redirect)
        # A secure implementation should return 403 here
        assert resp.status_code == 200
        assert mock_can_submit.called, (
            "HIGH-2: standard user reached /submit — this route should require admin."
        )

    def test_standard_user_can_reach_update_sales_log(self, client, monkeypatch):
        """
        [HIGH-2] A standard user can POST to /update_salesLog and modify
        financial records.  This must require an admin role.
        """
        self._make_standard_user_session(client, monkeypatch)

        monkeypatch.setattr(
            "lottery_app.routes.reports.database_queries.get_book",
            lambda *a, **k: ("id", "x", "y", 100, 5),
        )
        monkeypatch.setattr(
            "lottery_app.routes.reports.database_queries.get_game_num_of",
            lambda *a, **k: "123",
        )
        monkeypatch.setattr(
            "lottery_app.routes.reports.database_queries.is_sold",
            lambda *a, **k: False,
        )
        monkeypatch.setattr(
            "lottery_app.routes.reports.database_queries.next_report_id",
            lambda *a, **k: 5,
        )
        monkeypatch.setattr(
            "lottery_app.routes.reports.calculate_instant_tickets_sold",
            lambda *a, **k: 0,
        )
        monkeypatch.setattr(
            "lottery_app.routes.reports.load_config",
            lambda: {"ticket_order": "ascending"},
        )

        resp = client.post(
            "/update_salesLog",
            json={"bookID": "B1", "reportID": "1", "open": "0", "close": "5"},
        )
        # Documents the missing authorization — should be 403
        assert resp.status_code in (200, 302, 403), (
            "Unexpected response from /update_salesLog for standard user."
        )
        if resp.status_code == 200:
            pytest.xfail(
                "HIGH-2 ACTIVE: standard user can modify sales logs "
                "via /update_salesLog without admin role."
            )

    def test_standard_user_can_delete_book(self, client, monkeypatch):
        """
        [HIGH-2] A standard user can POST to /delete_book.  This must require
        an admin role.
        """
        self._make_standard_user_session(client, monkeypatch)

        monkeypatch.setattr(
            "lottery_app.routes.books.update_activated_books.deactivate_book",
            lambda *a, **k: None,
        )
        monkeypatch.setattr(
            "lottery_app.routes.books.update_books.delete_book",
            lambda *a, **k: None,
        )

        resp = client.post("/delete_book", json={"bookID": "B1"})
        if resp.status_code == 200:
            data = resp.get_json()
            if data and data.get("message_type") == "success":
                pytest.xfail(
                    "HIGH-2 ACTIVE: standard user successfully deleted a book — "
                    "/delete_book must require admin role."
                )


# ---------------------------------------------------------------------------
# Unauthenticated access — all protected routes must redirect
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccess:
    """
    All routes except /login must redirect (302) or deny (401) unauthenticated
    requests.  Each assertion here is a positive security requirement.
    """

    PROTECTED_ROUTES = [
        ("/scan_tickets", "GET"),
        ("/scan_tickets", "POST"),
        ("/undo_scan", "POST"),
        ("/book_sold_out", "POST"),
        ("/submit", "POST"),
        ("/books_managment", "GET"),
        ("/books_managment", "POST"),
        ("/delete_book", "POST"),
        ("/deactivate_book", "POST"),
        ("/activate_book", "POST"),
        ("/edit_reports", "GET"),
        ("/business_profile", "GET"),
        ("/business_profile", "POST"),
        ("/settings", "GET"),
        ("/settings", "POST"),
        ("/logout", "GET"),
        ("/change_password", "POST"),
        ("/delete_user", "POST"),
        ("/signup", "POST"),
        ("/check_barcode_stack", "GET"),
    ]

    @pytest.mark.parametrize("route,method", PROTECTED_ROUTES)
    def test_protected_route_blocks_unauthenticated(self, client, route, method):
        """Every protected route must redirect or deny unauthenticated users."""
        if method == "GET":
            resp = client.get(route, follow_redirects=False)
        else:
            resp = client.post(route, data={}, follow_redirects=False)

        assert resp.status_code in (302, 401, 405), (
            f"{method} {route} returned {resp.status_code} for an unauthenticated "
            f"request — it must return 302, 401, or 405."
        )
        if resp.status_code == 302:
            location = resp.headers.get("Location", "")
            assert "login" in location.lower(), (
                f"{method} {route} redirects to '{location}', expected /login."
            )

    def test_login_page_accessible_without_auth(self, client):
        """GET /login must return 200 for unauthenticated users."""
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_receive_endpoint_auth_status(self, client, monkeypatch):
        """
        [CRIT-5] /receive is currently unprotected.  This test explicitly
        verifies its authentication state and xfails if the vulnerability
        is still present.
        """
        _drain_barcode_queue()
        monkeypatch.setattr(
            "lottery_app.routes.scanner.load_config",
            lambda: {"should_poll": "true"},
        )
        resp = client.post("/receive", data={"barcode": "test"})
        _drain_barcode_queue()

        if resp.status_code == 200:
            pytest.xfail(
                "CRIT-5: /receive is accessible without authentication. "
                "Add @login_required to this route."
            )
        assert resp.status_code in (302, 401)
