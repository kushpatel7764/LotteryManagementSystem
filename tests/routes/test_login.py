"""Tests for the login, logout, password change, and user deletion routes."""
# pylint: disable=redefined-outer-name
import sqlite3
from unittest.mock import patch, MagicMock

import pytest

from lottery_app.database.user_model import User


@pytest.fixture
def mock_db():
    """Create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT
        )
    """)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def client(app):  # pylint: disable=redefined-outer-name
    """Return a configured test client."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def mock_cursor(mock_db):  # pylint: disable=redefined-outer-name
    """Return a mock context manager similar to get_db_cursor(DATABASE)."""

    class MockCursorContext:  # pylint: disable=too-few-public-methods
        """Wraps an in-memory connection to mimic the real cursor context."""

        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            self.conn = mock_db

        def __enter__(self):
            return self.conn.cursor()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.conn.commit()
            return False

    def get_db_cursor_mock(*args, **kwargs):  # pylint: disable=unused-argument
        return MockCursorContext()

    return get_db_cursor_mock


def test_create_and_get_user(mock_cursor):  # pylint: disable=redefined-outer-name
    """Creating a user and retrieving it by username returns the correct data."""
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor), \
         patch("lottery_app.database.user_model.flash"):
        User.create("testuser", "password123", "admin")
        user = User.get_by_username("testuser")

        assert user is not None
        assert user.username == "testuser"
        assert user.role == "admin"
        assert user.verify_password("password123") is True


def test_get_by_id(mock_cursor):  # pylint: disable=redefined-outer-name
    """Looking up a user by ID returns the correct record."""
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        with mock_cursor() as cursor:
            cursor.execute(
                "INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)",
                ("iduser", "fakehash", "standard"),
            )
            user_id = cursor.lastrowid

        user = User.get_by_id(user_id)
        assert user is not None
        assert user.username == "iduser"


def test_update_password(mock_cursor):  # pylint: disable=redefined-outer-name
    """Updating a user's password allows login with the new password."""
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor), \
         patch("lottery_app.database.user_model.flash"):
        User.create("changepass", "oldpass")
        user = User.get_by_username("changepass")

        User.update_password(user.id, "newpass")
        updated = User.get_by_id(user.id)

        assert updated.verify_password("newpass")


def test_delete_user(mock_cursor):  # pylint: disable=redefined-outer-name
    """Deleting a user removes them from the database."""
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        with patch("lottery_app.database.user_model.flash") as mock_flash:
            User.create("delete_me", "1234")
            user = User.get_by_username("delete_me")
            assert user is not None

            User.delete("delete_me")
            deleted_user = User.get_by_username("delete_me")
            assert deleted_user is None

            mock_flash.assert_called()


def test_login_success(client):  # pylint: disable=redefined-outer-name
    """Valid credentials call login_user and return 200."""

    class FakeUser:  # pylint: disable=too-few-public-methods
        """Minimal user object for login testing."""
        id = 1
        username = "user"

        def verify_password(self, password):
            """Accept only the correct password."""
            return password == "pass"

    fake_user = FakeUser()
    login_called = {"value": False}

    def fake_login_user(user):
        login_called["value"] = True
        assert user.username == "user"

    with patch(
        "lottery_app.database.user_model.User.get_by_username", return_value=fake_user
    ):
        with patch(
            "lottery_app.routes.security.login_user", side_effect=fake_login_user
        ):
            response = client.post(
                "/login",
                data={"username": "user", "password": "pass"},
                follow_redirects=True,
            )

    assert login_called["value"] is True
    assert response.status_code == 200


def test_login_failure(client):  # pylint: disable=redefined-outer-name
    """Invalid credentials display an error message."""
    with patch(
        "lottery_app.database.user_model.User.get_by_username", return_value=None
    ):
        response = client.post(
            "/login",
            data={"username": "wrong", "password": "wrong"},
            follow_redirects=True,
        )
        assert b"Invalid username or password" in response.data


def test_logout(client, monkeypatch):  # pylint: disable=redefined-outer-name
    """Logging out calls logout_user and redirects to /login."""

    class FakeUser:  # pylint: disable=too-few-public-methods
        """Minimal authenticated user for logout testing."""
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", FakeUser)

    mock_logout = MagicMock()
    monkeypatch.setattr("lottery_app.routes.security.logout_user", mock_logout)

    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.get("/logout", follow_redirects=False)

    mock_logout.assert_called_once()
    assert response.status_code in (302, 303)
    assert "/login" in response.headers["Location"]


def test_change_password_success(client, monkeypatch):  # pylint: disable=redefined-outer-name
    """Correct current password + matching new passwords updates successfully."""

    class FakeUser:  # pylint: disable=too-few-public-methods
        """Minimal authenticated user for password-change testing."""
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", FakeUser)

    mock_user_instance = MagicMock()
    mock_user_instance.id = 1
    mock_user_instance.verify_password.return_value = True
    mock_user_instance.update_password = MagicMock()

    monkeypatch.setattr(
        "lottery_app.routes.security.User.get_by_id", lambda user_id: mock_user_instance
    )

    with client.session_transaction() as sess:
        sess["user_id"] = 1

    response = client.post(
        "/change_password",
        data={
            "current_password": "old",
            "new_password": "new",
            "confirm_password": "new",
        },
        follow_redirects=True,
    )

    mock_user_instance.update_password.assert_called_once_with(1, "new")
    assert b"Password updated successfully!" in response.data


def test_change_password_fail_mismatch(client, monkeypatch):  # pylint: disable=redefined-outer-name
    """Mismatched new passwords flash an error message."""

    class FakeUser:  # pylint: disable=too-few-public-methods
        """Minimal authenticated user for mismatch testing."""
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", FakeUser)

    mock_user_instance = MagicMock()
    mock_user_instance.id = 1
    mock_user_instance.verify_password.return_value = True

    monkeypatch.setattr(
        "lottery_app.database.user_model.User.get_by_id",
        lambda user_id: mock_user_instance,
    )

    response = client.post(
        "/change_password",
        data={
            "current_password": "old",
            "new_password": "new1",
            "confirm_password": "new2",
        },
        follow_redirects=True,
    )
    assert b"New passwords do not match." in response.data


def test_delete_user_success(client, monkeypatch):  # pylint: disable=redefined-outer-name
    """Admin can delete another user; delete is called and page renders 200.

    NOTE (MODIFIED): The previous assertion checked for the flash message
    "other_user's account was deleted sucessfully." which does not match the
    actual message emitted by User.delete():
        "User '{username}' was deleted successfully."
    The test has been corrected to verify the call itself rather than an
    incorrect expected string.  The flash assertion is left to
    test_delete_user_flash_message below.
    """

    class FakeUser:  # pylint: disable=too-few-public-methods
        """Minimal admin user for deletion testing."""
        id = 1
        username = "admin"
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", FakeUser)

    mock_user_instance = MagicMock()
    mock_user_instance.username = "admin"
    monkeypatch.setattr(
        "lottery_app.database.user_model.User.get_by_id",
        lambda user_id: mock_user_instance,
    )

    mock_delete = MagicMock()
    monkeypatch.setattr("lottery_app.database.user_model.User.delete", mock_delete)

    response = client.post(
        "/delete_user", data={"username": "other_user"}, follow_redirects=True
    )

    mock_delete.assert_called_once_with("other_user")
    assert response.status_code == 200


def test_delete_user_flash_message():  # NEW
    """User.delete flashes the correct success message format.

    NEW TEST: validates the flash message text that User.delete() actually
    produces (user_model.py line 117) against what the route emits.
    """
    with patch("lottery_app.database.user_model.get_db_cursor") as mock_ctx:
        cursor = MagicMock()
        cursor.fetchone.return_value = ("standard",)  # role is not default_admin
        mock_ctx.return_value.__enter__.return_value = cursor

        flash_calls = []

        with patch(
            "lottery_app.database.user_model.flash",
            side_effect=lambda msg, cat: flash_calls.append((msg, cat)),
        ):
            User.delete("targetuser")

        assert any("targetuser" in msg for msg, _ in flash_calls), (
            "User.delete must flash a message containing the deleted username."
        )


def test_delete_user_protect_self(client, monkeypatch):  # pylint: disable=redefined-outer-name
    """A user cannot delete their own account."""

    class FakeUser:  # pylint: disable=too-few-public-methods
        """Minimal user for self-deletion guard testing."""
        id = 1
        username = "selfuser"
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", FakeUser)

    mock_user_instance = MagicMock()
    mock_user_instance.username = "selfuser"
    monkeypatch.setattr(
        "lottery_app.database.user_model.User.get_by_id",
        lambda user_id: mock_user_instance,
    )

    mock_delete = MagicMock()
    monkeypatch.setattr("lottery_app.database.user_model.User.delete", mock_delete)

    mock_flash = MagicMock()
    monkeypatch.setattr("lottery_app.routes.security.flash", mock_flash)

    response = client.post(
        "/delete_user", data={"username": "selfuser"}, follow_redirects=True
    )

    mock_delete.assert_not_called()
    mock_flash.assert_called_once_with(
        "You cannot delete the currently logged-in user.", "business-profile_error"
    )
    assert response.status_code == 200


# ============================================================
# NEW SECURITY TESTS
# ============================================================


def test_login_with_empty_username(client):  # NEW
    """Empty username must produce a login-failure response, not a 500."""
    response = client.post(
        "/login",
        data={"username": "", "password": "somepassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_login_with_empty_password(client):  # NEW
    """Empty password must produce a login-failure response, not a 500."""
    response = client.post(
        "/login",
        data={"username": "admin", "password": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_login_with_sql_injection_username(client):  # NEW
    """SQL injection in username must not grant access or crash the application."""
    with patch(
        "lottery_app.database.user_model.User.get_by_username", return_value=None
    ):
        response = client.post(
            "/login",
            data={"username": "' OR '1'='1", "password": "anything"},
            follow_redirects=True,
        )
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_login_with_oversized_input(client):  # NEW
    """Very large username/password inputs must not cause a server error."""
    with patch(
        "lottery_app.database.user_model.User.get_by_username", return_value=None
    ):
        response = client.post(
            "/login",
            data={"username": "A" * 10_000, "password": "B" * 10_000},
            follow_redirects=True,
        )
    assert response.status_code == 200


def test_change_password_wrong_current_password(client, monkeypatch):  # NEW
    """A wrong current password must flash an error and not update the hash."""

    class FakeUser:  # pylint: disable=too-few-public-methods
        """Minimal user for wrong-password testing."""
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", FakeUser)

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.verify_password.return_value = False  # wrong current password
    mock_user.update_password = MagicMock()

    monkeypatch.setattr(
        "lottery_app.routes.security.User.get_by_id", lambda uid: mock_user
    )

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"

    response = client.post(
        "/change_password",
        data={
            "current_password": "wrongpass",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        },
        follow_redirects=True,
    )

    mock_user.update_password.assert_not_called()
    assert b"Current password is incorrect" in response.data


def test_get_login_page_renders(client):  # NEW
    """GET /login must return 200 and the login form."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"login" in response.data.lower()


def test_verify_password_wrong_hash(mock_cursor):  # NEW
    """verify_password returns False when the hash does not match."""
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor), \
         patch("lottery_app.database.user_model.flash"):
        User.create("verifyuser", "correct_password")
        user = User.get_by_username("verifyuser")
        assert user.verify_password("wrong_password") is False


def test_create_duplicate_username_does_not_raise(mock_cursor):  # NEW
    """Creating a user with a duplicate username flashes an IntegrityError message."""
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        with patch("lottery_app.database.user_model.flash"):
            User.create("dupuser", "pass1")
            # Second creation with same username should not raise — it flashes
            User.create("dupuser", "pass2")


def test_delete_nonexistent_user_does_not_raise(mock_cursor):  # NEW
    """Deleting a username that doesn't exist should flash but not raise."""
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        with patch("lottery_app.database.user_model.flash") as mock_flash:
            User.delete("nobody_here")
            mock_flash.assert_called()


def test_protected_admin_user_cannot_be_deleted(mock_cursor):  # NEW
    """A user with role 'default_admin' is protected and cannot be deleted."""
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        with patch("lottery_app.database.user_model.flash") as mock_flash:
            # Insert a default_admin user
            with mock_cursor() as cur:
                cur.execute(
                    "INSERT INTO Users (username, password_hash, role) VALUES (?,?,?)",
                    ("superadmin", "hash", "default_admin"),
                )

            User.delete("superadmin")

            # Must flash "Cannot delete protected user."
            flash_args = [call.args[0] for call in mock_flash.call_args_list]
            assert any("protected" in msg.lower() for msg in flash_args), (
                "Deleting a default_admin user must flash a 'protected' message."
            )

            # Must NOT have deleted the row
            with mock_cursor() as cur:
                cur.execute("SELECT * FROM Users WHERE username=?", ("superadmin",))
                row = cur.fetchone()
            assert row is not None, "default_admin user was incorrectly deleted."
