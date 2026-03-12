import os
import tempfile
import pytest
import json
import pytest
from lottery_app.utils import config as config_updates
from unittest.mock import MagicMock
from lottery_app import create_app
from lottery_app.database import setup_database
from lottery_app.database.user_model import User

@pytest.fixture
def app():
    db_fd, temp_db = tempfile.mkstemp()

    import lottery_app.utils.config
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
    return app.test_client()


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username="testuser", password="testpassword"):
        return self._client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self._client.get("/logout", follow_redirects=True)


@pytest.fixture
def auth(client):
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
    def _assert(matcher, expected):
        matcher(expected)
    return _assert

