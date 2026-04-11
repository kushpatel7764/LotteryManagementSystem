"""Shared pytest fixtures and helpers for the lottery app test suite."""

import json
import os
import sqlite3
import tempfile
from unittest.mock import MagicMock

import pytest

import lottery_app.utils.config
from lottery_app import create_app
from lottery_app.database import setup_database
from lottery_app.database.setup_database import initialize_database
from lottery_app.database.user_model import User

# pylint: disable=redefined-outer-name

SCHEMA_SQL = "lottery_app/database/Lottery_DB_Schema.sql"  # adjust if needed


@pytest.fixture
def temp_db(tmp_path):
    """Return a path to a temporary SQLite database file."""
    db_path = tmp_path / "test.db"
    return str(db_path)


@pytest.fixture
def sample_ticket_info():
    """Return a sample ticket info dictionary for testing."""
    return {
        "ActiveBookID": "BOOK123",
        "prev_TicketNum": 100,
        "current_TicketNum": 90,
        "Ticket_Name": "Lucky 7",
        "Ticket_GameNumber": "G123",
    }


@pytest.fixture
def db_path(tmp_path):
    """Return the path to a temporary database file."""
    return str(tmp_path / "test.db")


@pytest.fixture
def db_cursor(db_path):
    """Yield an SQLite cursor connected to an initialized test database."""
    initialize_database(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    yield cursor
    conn.commit()
    conn.close()


@pytest.fixture
def app():
    """Create and configure a Flask app instance backed by a temporary database."""
    db_fd, temp_db = tempfile.mkstemp()

    lottery_app.utils.config.db_path = temp_db

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    # Initialize schema in temp db
    setup_database.initialize_database(temp_db)

    # Only create if it doesn't exist
    if not User.get_by_username("testuser"):
        User.create("testuser", "testpassword", role="admin")

    yield app

    os.close(db_fd)
    os.unlink(temp_db)


@pytest.fixture
def client(app):
    """Return a Flask test client for the app fixture."""
    return app.test_client()


class AuthActions:
    """Helper class for performing login/logout actions in tests."""

    def __init__(self, client):
        """Initialize with a Flask test client."""
        self._client = client

    def login(self, username="testuser", password="testpassword"):
        """Post login credentials and follow redirects."""
        return self._client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        """Send a logout request and follow redirects."""
        return self._client.get("/logout", follow_redirects=True)


@pytest.fixture
def auth(client):
    """Return an AuthActions helper bound to the test client."""
    return AuthActions(client)


# -------------------------------------------------------------------
# Helper: assert JSON written correctly
# -------------------------------------------------------------------
def assert_json_written(m, expected_dict):
    """Ensure JSON content written to mock_open matches expected dict."""
    written_data = "".join(call.args[0] for call in m().write.call_args_list)
    assert json.loads(written_data) == expected_dict


# -------------------------------------------------------------------
# Fixture: mock load_config + flash + open()
# factory style fixture
# -------------------------------------------------------------------
@pytest.fixture
def update_env(monkeypatch, tmp_path):
    """
    Fixture that creates a fake config environment for update_* tests.
    Returns helper function to initialize config + mocks.
    """

    def _env(initial_config):
        json_path = tmp_path / "config.json"

        # Write initial config
        json_path.write_text(json.dumps(initial_config))

        # Mock CONFIG_PATH to point to temp file
        monkeypatch.setattr("lottery_app.utils.config.CONFIG_PATH", str(json_path))

        # Mock flash
        flash_mock = MagicMock()
        monkeypatch.setattr("lottery_app.utils.config.flash", flash_mock)

        # Mock load_config to read test file
        def load_cfg():
            return json.loads(json_path.read_text())

        monkeypatch.setattr("lottery_app.utils.config.load_config", load_cfg)

        # Helper for asserting json updates
        def matcher(expected):
            actual = json.loads(json_path.read_text())
            assert actual == expected

        return load_cfg, flash_mock, matcher

    return _env


# Make helper available globally to all tests
@pytest.fixture
def json_assert():
    """Return a callable that asserts a matcher against an expected value."""
    def _assert(matcher, expected):
        matcher(expected)

    return _assert
