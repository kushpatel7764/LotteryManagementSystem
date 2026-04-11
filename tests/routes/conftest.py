"""Shared pytest fixtures for the routes test suite."""
import json
import os
import tempfile
from unittest.mock import MagicMock

import pytest
from flask import template_rendered

from lottery_app import create_app
from lottery_app.database import setup_database
from lottery_app.database.user_model import User


@pytest.fixture
def app():
    """Create a Flask test app backed by a temporary SQLite database."""
    db_fd, temp_db = tempfile.mkstemp()

    import lottery_app.utils.config  # pylint: disable=import-outside-toplevel

    lottery_app.utils.config.db_path = temp_db

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    setup_database.initialize_database(temp_db)

    if not User.get_by_username("testuser"):
        User.create("testuser", "testpassword", role="admin")

    yield flask_app

    os.close(db_fd)
    os.unlink(temp_db)


@pytest.fixture
def client(app):  # pylint: disable=redefined-outer-name
    """Return a test client for the given app."""
    return app.test_client()


class AuthActions:
    """Helper class for login/logout actions in route tests."""

    def __init__(self, client):  # pylint: disable=redefined-outer-name
        self._client = client

    def login(self, username="testuser", password="testpassword"):
        """POST login credentials and follow the redirect."""
        return self._client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        """GET the logout endpoint and follow the redirect."""
        return self._client.get("/logout", follow_redirects=True)


@pytest.fixture
def auth(client):  # pylint: disable=redefined-outer-name
    """Return an AuthActions helper bound to the given test client."""
    return AuthActions(client)


@pytest.fixture
def captured_templates(app):  # pylint: disable=redefined-outer-name
    """Capture every rendered template and its context during a test."""
    recorded = []

    def record(_sender, template, context, **_extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


# -------------------------------------------------------------------
# Helper: assert JSON written correctly
# -------------------------------------------------------------------
def assert_json_written(m, expected_dict):
    """Ensure JSON content written to mock_open matches expected dict."""
    written_data = "".join(call.args[0] for call in m().write.call_args_list)
    assert json.loads(written_data) == expected_dict


# -------------------------------------------------------------------
# Fixture: mock load_config + flash + open()  (factory style)
# -------------------------------------------------------------------
@pytest.fixture
def update_env(monkeypatch, tmp_path):
    """
    Factory fixture for update_* tests.

    Returns a helper function that writes an initial config to a temp
    file and wires up monkeypatches for CONFIG_PATH, flash, and
    load_config.  The helper itself returns (load_cfg, flash_mock,
    matcher) so callers can assert on the final file state.
    """

    def _env(initial_config):
        json_path = tmp_path / "config.json"
        json_path.write_text(json.dumps(initial_config))

        monkeypatch.setattr("lottery_app.utils.config.CONFIG_PATH", str(json_path))

        flash_mock = MagicMock()
        monkeypatch.setattr("lottery_app.utils.config.flash", flash_mock)

        def load_cfg():
            return json.loads(json_path.read_text())

        monkeypatch.setattr("lottery_app.utils.config.load_config", load_cfg)

        def matcher(expected):
            actual = json.loads(json_path.read_text())
            assert actual == expected

        return load_cfg, flash_mock, matcher

    return _env


@pytest.fixture
def json_assert():
    """Return a helper that delegates to a matcher callable."""
    def _assert(matcher, expected):
        matcher(expected)

    return _assert
