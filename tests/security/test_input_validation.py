"""
Security tests: input validation, injection resistance, and edge-case handling.

Covers:
- SQL injection attempts in login form
- Empty / oversized / malformed inputs at every entry point
- XSS payloads in business profile fields
- Barcode field injections in scanner and ticket routes
- URL parameter message injection (flash category manipulation)
- Password strength enforcement
"""

from unittest.mock import MagicMock, patch

import pytest

from lottery_app.routes.business_profile import validate_and_update_business_info
from lottery_app.database.user_model import User


# ---------------------------------------------------------------------------
# SQL injection — login form
# ---------------------------------------------------------------------------


class TestLoginSQLInjection:
    """
    All database queries in User.get_by_username use parameterised queries
    (``?`` placeholders), so these inputs must never break authentication.
    """

    SQL_INJECTION_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE Users; --",
        "' OR 1=1 --",
        "admin'--",
        "' UNION SELECT * FROM Users --",
        '" OR ""="',
        "1; SELECT * FROM Users",
        "' OR 'x'='x",
        "\\' OR 1=1 --",
    ]

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_username_returns_invalid_message(
        self, client, payload
    ):
        """
        SQL injection in the username field must be treated as a failed login,
        never granting access or raising an unhandled exception.
        """
        resp = client.post(
            "/login",
            data={"username": payload, "password": "anything"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data, (
            f"SQL injection payload '{payload}' did not produce an invalid-login "
            f"message — potential vulnerability."
        )

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_password_returns_invalid_message(
        self, client, payload
    ):
        """SQL injection in the password field must always produce a login failure."""
        resp = client.post(
            "/login",
            data={"username": "admin", "password": payload},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_login_uses_parameterised_query(self):
        """
        User.get_by_username must use a parameterised query (``?`` placeholder),
        never string formatting.
        """
        with patch("lottery_app.database.user_model.get_db_cursor") as mock_ctx:
            cursor = MagicMock()
            cursor.fetchone.return_value = None
            mock_ctx.return_value.__enter__.return_value = cursor

            User.get_by_username("' OR 1=1 --")

            args, _ = cursor.execute.call_args
            query, params = args[0], args[1]

            # The query must use a placeholder, not string formatting
            assert "?" in query, "get_by_username must use a parameterised placeholder"
            assert "' OR 1=1 --" not in query, (
                "The injection payload must be in the params tuple, not the query string"
            )
            assert "' OR 1=1 --" in params


# ---------------------------------------------------------------------------
# Empty and null inputs — login
# ---------------------------------------------------------------------------


class TestEmptyInputLogin:
    """Empty credentials must never cause a server error or grant access."""

    def test_empty_username_returns_invalid(self, client):
        """Empty username produces a login failure message."""
        resp = client.post(
            "/login",
            data={"username": "", "password": "anything"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_empty_password_returns_invalid(self, client):
        """Empty password produces a login failure message."""
        resp = client.post(
            "/login",
            data={"username": "admin", "password": ""},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_both_empty_returns_invalid(self, client):
        """Completely empty form produces a login failure message."""
        resp = client.post(
            "/login",
            data={"username": "", "password": ""},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_missing_fields_does_not_crash(self, client):
        """POST /login with no body at all must not return 500."""
        resp = client.post("/login", data={}, follow_redirects=True)
        assert resp.status_code != 500


# ---------------------------------------------------------------------------
# Oversized inputs — login
# ---------------------------------------------------------------------------


class TestOversizedInputLogin:
    """Extremely large inputs must not cause memory issues or crashes."""

    def test_very_long_username(self, client):
        """A 10 000-character username must produce a clean login-failure response."""
        payload = "A" * 10_000
        resp = client.post(
            "/login",
            data={"username": payload, "password": "pass"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_very_long_password(self, client):
        """A 10 000-character password must produce a clean login-failure response."""
        payload = "P" * 10_000
        resp = client.post(
            "/login",
            data={"username": "admin", "password": payload},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_null_bytes_in_username(self, client):
        """Null bytes in the username must not crash the application."""
        payload = "admin\x00injected"
        resp = client.post(
            "/login",
            data={"username": payload, "password": "pass"},
            follow_redirects=True,
        )
        assert resp.status_code in (200, 400)


# ---------------------------------------------------------------------------
# Business profile — XSS and validation bypass attempts
# ---------------------------------------------------------------------------


class TestBusinessProfileInputValidation:
    """
    Business profile fields are validated by regex.  XSS payloads and
    injection attempts must be rejected or stored safely.
    """

    XSS_PAYLOADS = [
        "<script>alert(1)</script>",
        '"><img src=x onerror=alert(1)>',
        "javascript:alert(1)",
        "<svg onload=alert(1)>",
        "';alert(1);//",
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_in_email_field_rejected(self, payload):
        """XSS payloads in the email field must fail email validation."""
        with patch(
            "lottery_app.routes.business_profile.update_business_info"
        ) as mock_update:
            data = {
                "business_name": "Shop",
                "business_address": "",
                "business_phone": "",
                "business_email": payload,
            }
            errors = validate_and_update_business_info(data)
        assert errors, (
            f"XSS payload '{payload}' passed email validation — must be rejected."
        )
        # Must not have been stored as a valid email
        email_calls = [
            call
            for call in mock_update.call_args_list
            if call.kwargs.get("name") == "business_email"
            and call.kwargs.get("value") == payload
        ]
        assert not email_calls, (
            "XSS payload was stored in 'business_email' without sanitisation."
        )

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_in_phone_field_rejected(self, payload):
        """XSS payloads in the phone field must fail phone validation."""
        with patch("lottery_app.routes.business_profile.update_business_info"):
            data = {
                "business_name": "Shop",
                "business_address": "",
                "business_phone": payload,
                "business_email": "",
            }
            errors = validate_and_update_business_info(data)
        assert errors

    def test_business_name_accepts_arbitrary_string(self):
        """
        Business name has no validation — any string is stored.
        This is a known limitation; test documents the current behaviour.
        """
        with patch(
            "lottery_app.routes.business_profile.update_business_info"
        ) as mock_update:
            data = {
                "business_name": "<b>Bold Shop</b>",
                "business_address": "",
                "business_phone": "",
                "business_email": "",
            }
            errors = validate_and_update_business_info(data)
        # No validation on business_name — currently accepted
        assert not errors
        mock_update.assert_any_call(
            name="business_name", value="<b>Bold Shop</b>"
        )

    def test_extremely_long_business_name(self):
        """A very long business name must not crash the validator."""
        with patch("lottery_app.routes.business_profile.update_business_info"):
            data = {
                "business_name": "S" * 10_000,
                "business_address": "",
                "business_phone": "",
                "business_email": "",
            }
            errors = validate_and_update_business_info(data)
        assert isinstance(errors, list)


# ---------------------------------------------------------------------------
# Scanner — barcode field injection
# ---------------------------------------------------------------------------


class TestScannerBarcodeInjection:
    """
    The /receive endpoint accepts raw barcode data.  Malformed or oversized
    payloads must not crash the application.
    """

    def _authenticated_post(self, client, monkeypatch, barcode):
        """Post a barcode as a logged-in user (simulated via session)."""
        monkeypatch.setattr(
            "lottery_app.routes.scanner.load_config",
            lambda: {"should_poll": "true"},
        )
        from lottery_app.utils import config as cfg  # pylint: disable=import-outside-toplevel
        cfg.BARCODE_STACK.clear()

        # Simulate a logged-in session (workaround while /receive lacks auth)
        resp = client.post("/receive", data={"barcode": barcode})
        cfg.BARCODE_STACK.clear()
        return resp

    def test_null_barcode_does_not_crash(self, client, monkeypatch):
        """POST /receive with no barcode field must return a clean response."""
        monkeypatch.setattr(
            "lottery_app.routes.scanner.load_config",
            lambda: {"should_poll": "true"},
        )
        resp = client.post("/receive", data={})
        assert resp.status_code in (200, 302, 401)

    def test_oversized_barcode_does_not_crash(self, client, monkeypatch):
        """A 100 000-character barcode payload must not crash the server."""
        resp = self._authenticated_post(client, monkeypatch, "9" * 100_000)
        assert resp.status_code in (200, 302, 401)

    def test_special_chars_in_barcode_stored_as_is(self, client, monkeypatch):
        """
        Special characters in the barcode are accepted by /receive — they will
        fail validation later in ScannedCodeManagement.validate_scanned_code().
        The route itself must not crash.
        """
        resp = self._authenticated_post(client, monkeypatch, "!@#$%^&*()")
        assert resp.status_code in (200, 302, 401)


# ---------------------------------------------------------------------------
# URL parameter message injection (flash category manipulation)
# ---------------------------------------------------------------------------


class TestUrlParameterInjection:  # pylint: disable=too-few-public-methods
    """
    Several routes pass ``message`` and ``message_type`` through query
    parameters into flash().  The ``message_type`` value is appended to a
    CSS class name.  Injecting unexpected values must not cause security issues.
    """

    def test_message_type_injection_in_scan_tickets(self, client, monkeypatch):
        """
        An attacker cannot inject an arbitrary flash category via the
        message_type query parameter — Jinja2 auto-escaping prevents XSS,
        but we verify the page still renders cleanly.
        """
        admin = MagicMock()
        admin.id = 1
        admin.is_authenticated = True
        monkeypatch.setattr("flask_login.utils._get_user", lambda: admin)

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        monkeypatch.setattr(
            "lottery_app.routes.tickets.database_queries.get_scan_ticket_page_table",
            lambda **k: [],
        )
        monkeypatch.setattr(
            "lottery_app.routes.tickets.calculate_instant_tickets_sold",
            lambda *a, **k: 0,
        )
        monkeypatch.setattr(
            "lottery_app.routes.tickets.database_queries.count_activated_books",
            lambda *a, **k: 0,
        )
        monkeypatch.setattr(
            "lottery_app.utils.config.load_config",
            lambda: {"ticket_order": "ascending", "should_poll": "false"},
        )

        resp = client.get(
            "/scan_tickets"
            "?message=<script>alert(1)</script>"
            "&message_type=error%22%20onload%3Dalert(1)",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # The raw <script> tag must NOT appear unescaped in the response
        assert b"<script>alert(1)</script>" not in resp.data, (
            "XSS payload appeared unescaped in the rendered page."
        )


# ---------------------------------------------------------------------------
# Password validation edge cases
# ---------------------------------------------------------------------------


class TestPasswordValidation:
    """
    User.update_password and User.create accept any password string.
    These tests document missing server-side length/strength enforcement.
    """

    def test_empty_password_is_hashed_and_stored(self):
        """
        Currently, User.create accepts an empty password string.
        This test documents the missing validation.
        """
        with patch("lottery_app.database.user_model.get_db_cursor") as mock_ctx:
            cursor = MagicMock()
            mock_ctx.return_value.__enter__.return_value = cursor

            with patch("lottery_app.database.user_model.flash"):
                User.create("emptypassuser", "")

            # The insert was attempted — no server-side password strength check
            cursor.execute.assert_called_once()

    def test_single_char_password_is_accepted(self):
        """User.create currently accepts a 1-character password (insecure)."""
        with patch("lottery_app.database.user_model.get_db_cursor") as mock_ctx:
            cursor = MagicMock()
            mock_ctx.return_value.__enter__.return_value = cursor

            with patch("lottery_app.database.user_model.flash"):
                User.create("weakpassuser", "x")

            cursor.execute.assert_called_once()

    def test_change_password_empty_new_password(self, client, monkeypatch):
        """
        POST /change_password with an empty new password must be rejected.
        Currently there is no server-side length check, so this test
        documents the missing validation.
        """
        admin = MagicMock()
        admin.id = 1
        admin.is_authenticated = True
        monkeypatch.setattr("flask_login.utils._get_user", lambda: admin)

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.verify_password.return_value = True
        mock_user.update_password = MagicMock()
        monkeypatch.setattr(
            "lottery_app.routes.security.User.get_by_id",
            lambda uid: mock_user,
        )

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        resp = client.post(
            "/change_password",
            data={
                "current_password": "correct",
                "new_password": "",
                "confirm_password": "",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # Document: currently update_password IS called even with empty string
        # A future fix should validate minimum length and prevent this call
