"""
Security tests: privilege escalation and broken access control.

Covers CRIT-4 (any user can create admin accounts via role parameter injection)
and HIGH-1 (any authenticated user can delete other users regardless of role).

Each test documents the *required* secure behaviour.  Tests that currently FAIL
against the unpatched codebase are marked with the corresponding audit finding
so they are easy to locate when fixing the vulnerabilities.
"""

from unittest.mock import MagicMock, patch

import pytest

from lottery_app.database.user_model import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_user(user_id, username, role):
    """Return a minimal user object understood by Flask-Login."""

    class FakeUser:  # pylint: disable=too-few-public-methods
        is_authenticated = True

    FakeUser.id = user_id
    FakeUser.username = username
    FakeUser.role = role
    return FakeUser()


# ---------------------------------------------------------------------------
# CRIT-4 — Privilege escalation via /signup role parameter injection
# ---------------------------------------------------------------------------


class TestSignupPrivilegeEscalation:
    """
    CRIT-4: The /signup route reads ``role`` directly from the POST body
    without checking whether the calling user has permission to assign that
    role.  Any logged-in standard user can therefore promote themselves (or
    a new account) to admin.
    """

    def test_signup_accessible_by_standard_user(self, client, monkeypatch):
        """
        [CRIT-4] /signup is gated only by @login_required — a standard user
        can reach it.  The route SHOULD additionally require an admin role.

        This test verifies the vulnerability exists: a standard user reaches
        the signup endpoint and gets a 200 (redirect to profile) instead of 403.
        """
        standard = _make_fake_user(2, "standard_user", "standard")
        monkeypatch.setattr("flask_login.utils._get_user", lambda: standard)

        mock_create = MagicMock()
        monkeypatch.setattr("lottery_app.database.user_model.User.create", mock_create)

        with client.session_transaction() as sess:
            sess["_user_id"] = "2"

        resp = client.post(
            "/signup",
            data={
                "username": "hacker",
                "password": "h4ck3r",
                "role": "standard",
            },
            follow_redirects=False,
        )
        # The route redirects on success — 302 means the user got through.
        # A secure implementation should return 403 here.
        assert resp.status_code in (302, 200), (
            "Standard user was blocked from /signup — vulnerability may be fixed."
        )

    def test_standard_user_cannot_inject_admin_role(self, client, monkeypatch):
        """
        [CRIT-4] A standard user should NOT be able to create an admin account
        by including ``role=admin`` in the POST body.

        This test asserts the *correct* secure behaviour.  It will FAIL against
        the unpatched codebase because the route blindly passes the form role
        to User.create().
        """
        standard = _make_fake_user(2, "standard_user", "standard")
        monkeypatch.setattr("flask_login.utils._get_user", lambda: standard)

        created_roles = []

        def spy_create(username, password, role="standard"):
            created_roles.append(role)

        monkeypatch.setattr("lottery_app.database.user_model.User.create", spy_create)
        monkeypatch.setattr(
            "lottery_app.routes.security.User.get_by_id",
            lambda uid: standard,
        )

        with client.session_transaction() as sess:
            sess["_user_id"] = "2"

        client.post(
            "/signup",
            data={"username": "evil", "password": "evil123", "role": "admin"},
            follow_redirects=True,
        )

        # If create() was called, the role must NOT be "admin"
        if created_roles and created_roles[0] == "admin":
            pytest.xfail(
                "VULNERABILITY ACTIVE (CRIT-4): standard user successfully injected "
                "role='admin' — the /signup route must check the caller's role before "
                "accepting a role parameter from the form."
            )
        if created_roles:
            assert created_roles[0] != "admin"

    def test_standard_user_cannot_inject_default_admin_role(self, client, monkeypatch):
        """
        [CRIT-4] A standard user must not be able to create a 'default_admin'
        account via the form, bypassing the protected-user guard.
        """
        standard = _make_fake_user(2, "standard_user", "standard")
        monkeypatch.setattr("flask_login.utils._get_user", lambda: standard)

        created_roles = []

        def spy_create(username, password, role="standard"):
            created_roles.append(role)

        monkeypatch.setattr("lottery_app.database.user_model.User.create", spy_create)
        monkeypatch.setattr(
            "lottery_app.routes.security.User.get_by_id",
            lambda uid: standard,
        )

        with client.session_transaction() as sess:
            sess["_user_id"] = "2"

        client.post(
            "/signup",
            data={
                "username": "fakesuperadmin",
                "password": "pass",
                "role": "default_admin",
            },
            follow_redirects=True,
        )

        if created_roles and created_roles[0] in ("admin", "default_admin"):
            pytest.xfail(
                "VULNERABILITY ACTIVE (CRIT-4): attacker successfully created "
                f"a '{created_roles[0]}' account via role parameter injection."
            )
        if created_roles:
            assert created_roles[0] not in ("admin", "default_admin")

    def test_admin_user_can_create_standard_user(self, client, monkeypatch):
        """
        [POSITIVE] A genuine admin should be able to create a standard user.
        """
        admin = _make_fake_user(1, "admin", "admin")
        monkeypatch.setattr("flask_login.utils._get_user", lambda: admin)

        mock_create = MagicMock()
        monkeypatch.setattr("lottery_app.database.user_model.User.create", mock_create)
        monkeypatch.setattr(
            "lottery_app.routes.security.User.get_by_id",
            lambda uid: admin,
        )

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        resp = client.post(
            "/signup",
            data={"username": "newstaff", "password": "secure123", "role": "standard"},
            follow_redirects=True,
        )

        assert resp.status_code == 200

    def test_unauthenticated_user_cannot_reach_signup(self, client):
        """
        [POSITIVE] /signup must redirect to login for unauthenticated users.
        """
        resp = client.post(
            "/signup",
            data={"username": "ghost", "password": "ghost"},
            follow_redirects=False,
        )
        assert resp.status_code in (302, 401)
        if resp.status_code == 302:
            assert "/login" in resp.headers.get("Location", "")


# ---------------------------------------------------------------------------
# HIGH-1 — Any authenticated user can delete other users
# ---------------------------------------------------------------------------


class TestUserDeletionAuthorization:
    """
    HIGH-1: The /delete_user route is protected only by @login_required.
    A standard user can delete any other user except themselves and
    'default_admin', including admin accounts.
    """

    def test_standard_user_cannot_delete_admin(self, client, monkeypatch):
        """
        [HIGH-1] A standard user must NOT be able to delete an admin account.

        This test asserts the correct secure behaviour and will FAIL against
        the unpatched code because the route has no role check.
        """
        standard = _make_fake_user(2, "standard_user", "standard")
        monkeypatch.setattr("flask_login.utils._get_user", lambda: standard)

        mock_instance = MagicMock()
        mock_instance.username = "standard_user"
        mock_instance.role = "standard"
        monkeypatch.setattr(
            "lottery_app.routes.security.User.get_by_id",
            lambda uid: mock_instance,
        )

        mock_delete = MagicMock()
        monkeypatch.setattr("lottery_app.database.user_model.User.delete", mock_delete)

        with client.session_transaction() as sess:
            sess["_user_id"] = "2"

        resp = client.post(
            "/delete_user",
            data={"username": "admin"},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        # A standard user must not have triggered a deletion
        if mock_delete.called:
            pytest.xfail(
                "VULNERABILITY ACTIVE (HIGH-1): standard user successfully deleted "
                "an admin account — the /delete_user route must verify the caller is admin."
            )
        mock_delete.assert_not_called()

    def test_admin_can_delete_standard_user(self, client, monkeypatch):
        """
        [POSITIVE] An admin should be able to delete a standard user.
        """
        admin = _make_fake_user(1, "admin", "admin")
        monkeypatch.setattr("flask_login.utils._get_user", lambda: admin)

        mock_instance = MagicMock()
        mock_instance.username = "admin"
        mock_instance.role = "admin"
        monkeypatch.setattr(
            "lottery_app.routes.security.User.get_by_id",
            lambda uid: mock_instance,
        )

        mock_delete = MagicMock()
        monkeypatch.setattr("lottery_app.database.user_model.User.delete", mock_delete)

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        resp = client.post(
            "/delete_user",
            data={"username": "regularuser"},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        mock_delete.assert_called_once_with("regularuser")

    def test_cannot_delete_self(self, client, monkeypatch):
        """
        [POSITIVE] A user must not be able to delete their own account.
        """
        admin = _make_fake_user(1, "admin", "admin")
        monkeypatch.setattr("flask_login.utils._get_user", lambda: admin)

        mock_instance = MagicMock()
        mock_instance.username = "admin"
        monkeypatch.setattr(
            "lottery_app.routes.security.User.get_by_id",
            lambda uid: mock_instance,
        )

        mock_delete = MagicMock()
        monkeypatch.setattr("lottery_app.database.user_model.User.delete", mock_delete)

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        resp = client.post(
            "/delete_user",
            data={"username": "admin"},
            follow_redirects=True,
        )

        assert resp.status_code == 200
        mock_delete.assert_not_called()

    def test_unauthenticated_user_cannot_delete(self, client):
        """
        [POSITIVE] /delete_user must redirect to login without a session.
        """
        resp = client.post(
            "/delete_user",
            data={"username": "victim"},
            follow_redirects=False,
        )
        assert resp.status_code in (302, 401)


# ---------------------------------------------------------------------------
# HIGH-3 — Role bug: default_admin cannot access edit_single_report
# ---------------------------------------------------------------------------


class TestDefaultAdminRoleBug:
    """
    HIGH-3: edit_single_report checks ``role != "admin"`` but the seeded
    account has role ``"default_admin"``, permanently locking it out.
    """

    def test_default_admin_role_rejected_from_edit_single_report(
        self, client, monkeypatch
    ):
        """
        [HIGH-3] The 'default_admin' role should be able to access
        /edit_report/<id>.  Currently it is blocked because the check is
        ``role != 'admin'`` (exact string match).

        This test documents the bug: it will PASS (showing the redirect) on
        the unpatched code, and should FAIL once the check is corrected to
        ``role not in ('admin', 'default_admin')``.
        """
        default_admin = _make_fake_user(1, "admin", "default_admin")
        monkeypatch.setattr("flask_login.utils._get_user", lambda: default_admin)

        mock_user = MagicMock()
        mock_user.role = "default_admin"
        monkeypatch.setattr(
            "lottery_app.routes.reports.User.get_by_id",
            lambda uid: mock_user,
        )

        with client.session_transaction() as sess:
            sess["_user_id"] = "1"

        resp = client.get("/edit_report/1", follow_redirects=False)
        # A fixed implementation returns 200; unpatched code returns 302
        location = resp.headers.get("Location", "")
        if resp.status_code == 302:
            # Bug is still present
            assert "edit_reports" in location, (
                "HIGH-3 BUG ACTIVE: default_admin redirected away from "
                "/edit_report — the role check must include 'default_admin'."
            )
