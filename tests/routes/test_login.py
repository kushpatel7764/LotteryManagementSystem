import pytest
import sqlite3
from unittest.mock import patch, MagicMock
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
def client(app):
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_cursor(mock_db):
    """Return a mock context manager similar to get_db_cursor(DATABASE)."""

    class MockCursorContext:
        def __init__(self, *args, **kwargs):
            # Accept any arguments like DATABASE
            self.conn = mock_db

        def __enter__(self):
            return self.conn.cursor()

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.conn.commit()
            return False

    # Return a callable that behaves like get_db_cursor()
    def get_db_cursor_mock(*args, **kwargs):
        return MockCursorContext()

    return get_db_cursor_mock


def test_create_and_get_user(mock_cursor):
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        User.create("testuser", "password123", "admin")
        user = User.get_by_username("testuser")

        assert user is not None
        assert user.username == "testuser"
        assert user.role == "admin"
        assert user.verify_password("password123") is True


def test_get_by_id(mock_cursor):
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        # Insert user manually
        with mock_cursor() as cursor:
            cursor.execute(
                "INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)",
                ("iduser", "fakehash", "standard"),
            )
            user_id = cursor.lastrowid

        user = User.get_by_id(user_id)
        assert user is not None
        assert user.username == "iduser"


def test_update_password(mock_cursor):
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        User.create("changepass", "oldpass")
        user = User.get_by_username("changepass")

        User.update_password(user.id, "newpass")
        updated = User.get_by_id(user.id)

        assert updated.verify_password("newpass")


def test_delete_user(mock_cursor):
    with patch("lottery_app.database.user_model.get_db_cursor", mock_cursor):
        with patch("lottery_app.database.user_model.flash") as mock_flash:
            User.create("delete_me", "1234")
            user = User.get_by_username("delete_me")
            assert user is not None

            User.delete("delete_me")
            deleted_user = User.get_by_username("delete_me")
            assert deleted_user is None

            mock_flash.assert_called()  # optional: verify flash was called


def test_login_success(client):
    # --- create a fake user object ---
    class FakeUser:
        id = 1
        username = "user"

        def verify_password(self, password):
            return password == "pass"

    fake_user = FakeUser()

    # Track whether login_user was called
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

    # --- Assertions ---
    assert login_called["value"] is True
    assert response.status_code == 200


def test_login_failure(client):
    with patch(
        "lottery_app.database.user_model.User.get_by_username", return_value=None
    ):
        response = client.post(
            "/login",
            data={"username": "wrong", "password": "wrong"},
            follow_redirects=True,
        )
        assert b"Invalid username or password" in response.data


def test_logout(client, monkeypatch):
    # -----------------------------
    # 1. Force user to be logged in
    # -----------------------------
    class FakeUser:
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: FakeUser())

    # -----------------------------
    # 2. Patch logout_user
    # -----------------------------
    mock_logout = MagicMock()
    monkeypatch.setattr("lottery_app.routes.security.logout_user", mock_logout)

    # -----------------------------
    # 3. Make GET request
    # -----------------------------
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # login session

    response = client.get("/logout", follow_redirects=False)

    # -----------------------------
    # 4. Assertions
    # -----------------------------
    mock_logout.assert_called_once()  # logout_user should be called

    # Redirect to login page
    assert response.status_code in (302, 303)
    assert "/login" in response.headers["Location"]


def test_change_password_success(client, monkeypatch):
    # 1. Force user to be logged in
    class FakeUser:
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: FakeUser())

    # 2. Mock User.get_by_id() to return a fake user instance
    mock_user_instance = MagicMock()
    mock_user_instance.id = 1
    mock_user_instance.verify_password.return_value = True
    # Patch the instance method
    mock_user_instance.update_password = MagicMock()

    monkeypatch.setattr(
        "lottery_app.routes.security.User.get_by_id", lambda user_id: mock_user_instance
    )

    # 3. Make POST request
    with client.session_transaction() as sess:
        sess["user_id"] = 1  # login session

    response = client.post(
        "/change_password",
        data={
            "current_password": "old",
            "new_password": "new",
            "confirm_password": "new",
        },
        follow_redirects=True,
    )

    # 4. Assert the instance method was called
    mock_user_instance.update_password.assert_called_once_with(1, "new")
    assert b"Password updated successfully!" in response.data


def test_change_password_fail_mismatch(client, monkeypatch):
    # -----------------------------
    # 1. Force user to be logged in
    # -----------------------------
    class FakeUser:
        id = 1
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: FakeUser())

    # -----------------------------------
    # 2. Mock User.get_by_id() to return a fake user instance
    # -----------------------------------
    mock_user_instance = MagicMock()
    mock_user_instance.id = 1
    mock_user_instance.verify_password.return_value = True

    monkeypatch.setattr(
        "lottery_app.database.user_model.User.get_by_id",
        lambda user_id: mock_user_instance,
    )
    # -----------------------------
    # 3. Make the POST request with mismatched passwords
    # -----------------------------
    response = client.post(
        "/change_password",
        data={
            "current_password": "old",
            "new_password": "new1",
            "confirm_password": "new2",
        },
        follow_redirects=True,
    )
    # -----------------------------
    # 4. Assert the flash message is present
    # -----------------------------
    assert b"New passwords do not match." in response.data


def test_delete_user_success(client, monkeypatch):
    # 1. Force user to be logged in
    class FakeUser:
        id = 1
        username = "admin"
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: FakeUser())

    # 2. Mock User.get_by_id()
    mock_user_instance = MagicMock()
    mock_user_instance.username = "admin"
    monkeypatch.setattr(
        "lottery_app.database.user_model.User.get_by_id",
        lambda user_id: mock_user_instance,
    )

    # 3. Mock User.delete
    mock_delete = MagicMock()
    monkeypatch.setattr("lottery_app.database.user_model.User.delete", mock_delete)

    # 4. Patch flash to capture messages
    mock_flash = MagicMock()
    monkeypatch.setattr("lottery_app.routes.security.flash", mock_flash)

    # 5. Make POST request
    response = client.post(
        "/delete_user", data={"username": "other_user"}, follow_redirects=True
    )

    # 6. Assertions
    mock_delete.assert_called_once_with("other_user")
    mock_flash.assert_called_once_with(
        "other_user's account was deleted sucessfully.", "business-profile_success"
    )
    assert response.status_code == 200


def test_delete_user_protect_self(client, monkeypatch):
    # 1. Fake logged-in user
    class FakeUser:
        id = 1
        username = "selfuser"
        is_authenticated = True

    monkeypatch.setattr("flask_login.utils._get_user", lambda: FakeUser())

    # 2. Mock User.get_by_id
    mock_user_instance = MagicMock()
    mock_user_instance.username = "selfuser"
    monkeypatch.setattr(
        "lottery_app.database.user_model.User.get_by_id",
        lambda user_id: mock_user_instance,
    )

    # 3. Mock User.delete
    mock_delete = MagicMock()
    monkeypatch.setattr("lottery_app.database.user_model.User.delete", mock_delete)

    # 4. Patch flash
    mock_flash = MagicMock()
    monkeypatch.setattr("lottery_app.routes.security.flash", mock_flash)

    # 5. Make POST request
    response = client.post(
        "/delete_user", data={"username": "selfuser"}, follow_redirects=True
    )

    # 6. Assertions
    mock_delete.assert_not_called()
    mock_flash.assert_called_once_with(
        "You cannot delete the currently logged-in user.", "business-profile_error"
    )
    assert response.status_code == 200
