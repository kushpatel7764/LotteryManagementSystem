"""Tests for the login, logout, password change, and user deletion routes."""
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
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
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
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
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
    """Admin can delete another user and receives a success flash."""

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

    mock_flash = MagicMock()
    monkeypatch.setattr("lottery_app.routes.security.flash", mock_flash)

    response = client.post(
        "/delete_user", data={"username": "other_user"}, follow_redirects=True
    )

    mock_delete.assert_called_once_with("other_user")
    mock_flash.assert_called_once_with(
        "other_user's account was deleted sucessfully.", "business-profile_success"
    )
    assert response.status_code == 200


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
