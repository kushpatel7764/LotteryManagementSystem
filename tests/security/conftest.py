"""
Shared fixtures for security tests.

Sets up the Flask test app with the FERNET_KEY from src/.env and patches
out the at-startup database decryption (which is irrelevant for unit tests
that use a temporary in-memory database).
"""

import os
import queue as _queue_mod
import tempfile
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from lottery_app import create_app
from lottery_app.database import setup_database
from lottery_app.database.user_model import User
from lottery_app.utils import config as config_module


def _load_fernet_key():
    """
    Try to read FERNET_KEY from src/.env, falling back to generating a
    fresh key when the file is absent (CI / clean-checkout scenarios).
    """
    env_path = os.path.join(
        os.path.dirname(__file__),  # tests/security/
        "..", "..",                  # project root
        "src", ".env",
    )
    env_path = os.path.abspath(env_path)

    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("FERNET_KEY="):
                    return line.split("=", 1)[1].strip()

    # No .env found — generate a temporary key for this test session
    return Fernet.generate_key().decode()


@pytest.fixture(scope="session", autouse=True)
def fernet_key_env():
    """
    Session-scoped fixture that ensures FERNET_KEY is set as an environment
    variable before any Flask app is created.  This prevents the
    ``cryptography.fernet.InvalidToken`` errors caused by create_app()
    generating a fresh key and then failing to decrypt an .enc file that was
    encrypted with a different key.
    """
    key = _load_fernet_key()
    original = os.environ.get("FERNET_KEY")
    os.environ["FERNET_KEY"] = key
    yield key
    if original is None:
        os.environ.pop("FERNET_KEY", None)
    else:
        os.environ["FERNET_KEY"] = original


@pytest.fixture
def app(fernet_key_env):  # pylint: disable=redefined-outer-name,unused-argument
    """
    Create a Flask test app backed by a temporary SQLite database.

    The db-decryption step inside create_app() is patched out because tests
    use their own temp database; there is no .enc file to decrypt.
    """
    db_fd, temp_db = tempfile.mkstemp()

    # Point the app at the temp database BEFORE create_app() runs
    config_module.db_path = temp_db

    # Patch where the names are *used* (lottery_app.__init__ imports them
    # directly, so we patch the names in that module's namespace).
    with patch("lottery_app.decrypt_file"), \
         patch("lottery_app.encrypt_file"):
        flask_app = create_app()

    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    setup_database.initialize_database(temp_db)

    # User.create() calls flash() which needs a request context
    with flask_app.test_request_context():
        if not User.get_by_username("testuser"):
            User.create("testuser", "testpassword", role="admin")

    yield flask_app

    os.close(db_fd)
    try:
        os.unlink(temp_db)
    except FileNotFoundError:
        pass


@pytest.fixture
def client(app):  # pylint: disable=redefined-outer-name
    """Return a Flask test client."""
    return app.test_client()


def _drain_barcode_queue():
    """Drain all items from BARCODE_QUEUE."""
    while not config_module.BARCODE_QUEUE.empty():
        try:
            config_module.BARCODE_QUEUE.get_nowait()
        except _queue_mod.Empty:
            break


@pytest.fixture(autouse=True)
def clear_barcode_queue():
    """Ensure BARCODE_QUEUE is empty before and after each test."""
    _drain_barcode_queue()
    yield
    _drain_barcode_queue()
