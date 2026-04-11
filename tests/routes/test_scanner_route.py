"""Tests for the scanner blueprint: /receive and /check_barcode_stack."""
import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin

from lottery_app.routes.scanner import scanner_bp
from lottery_app.utils import config as config_module

# ------------------------
# Test Helpers / Fixtures
# ------------------------


class TestUser(UserMixin):
    """Minimal user class for Flask-Login in scanner tests."""

    id = 1


@pytest.fixture
def app(monkeypatch):  # pylint: disable=unused-argument
    """Create a minimal Flask app with the scanner blueprint registered."""
    test_app = Flask(__name__)
    test_app.config["TESTING"] = True
    test_app.config["SECRET_KEY"] = "test-secret"

    login_manager = LoginManager()
    login_manager.init_app(test_app)

    @login_manager.user_loader
    def load_user(_user_id):  # pylint: disable=unused-argument
        return TestUser()

    test_app.register_blueprint(scanner_bp)

    yield test_app


@pytest.fixture
def client(app):  # pylint: disable=redefined-outer-name
    """Return a test client for the scanner app."""
    return app.test_client()


@pytest.fixture
def logged_in_client(client):  # pylint: disable=redefined-outer-name
    """
    Return a test client with a fake authenticated session.
    """
    with client.session_transaction() as session:
        session["_user_id"] = "1"
        session["_fresh"] = True
    return client


@pytest.fixture(autouse=True)
def clear_barcode_stack():
    """Ensure BARCODE_STACK is empty before and after each test."""
    config_module.BARCODE_STACK.clear()
    yield
    config_module.BARCODE_STACK.clear()


# ------------------------
# Tests for /receive
# ------------------------


def test_receive_barcode_polling_enabled(logged_in_client, monkeypatch):  # pylint: disable=redefined-outer-name
    """POST /receive with polling enabled pushes the barcode onto the stack."""
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )

    response = logged_in_client.post("/receive", data={"barcode": "123456"})

    assert response.status_code == 200
    assert response.data == b"Received"
    assert config_module.BARCODE_STACK == ["123456"]


def test_receive_barcode_polling_disabled(logged_in_client, monkeypatch):  # pylint: disable=redefined-outer-name
    """POST /receive with polling disabled ignores the barcode."""
    monkeypatch.setattr(config_module, "load_config", lambda: {"should_poll": "false"})

    response = logged_in_client.post("/receive", data={"barcode": "999999"})

    assert response.status_code == 200
    assert response.data == b"Ignored"
    assert not config_module.BARCODE_STACK


def test_receive_missing_barcode(logged_in_client, monkeypatch):  # pylint: disable=redefined-outer-name
    """POST /receive with no barcode field pushes None onto the stack."""
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )

    response = logged_in_client.post("/receive", data={})

    assert response.status_code == 200
    assert response.data == b"Received"
    assert config_module.BARCODE_STACK == [None]


def test_receive_requires_login(client):  # pylint: disable=redefined-outer-name
    """POST /receive without a session redirects or returns 401."""
    response = client.post("/receive", data={"barcode": "123"})

    assert response.status_code in (302, 401)


# ------------------------
# Tests for /check_barcode_stack
# ------------------------


def test_check_returns_latest_barcode(logged_in_client):  # pylint: disable=redefined-outer-name
    """GET /check_barcode_stack pops and returns the last barcode."""
    config_module.BARCODE_STACK.extend(["111", "222", "333"])

    response = logged_in_client.get("/check_barcode_stack")

    assert response.status_code == 200
    assert response.json == {"barcode": "333"}
    assert config_module.BARCODE_STACK == ["111", "222"]


def test_check_returns_none_when_empty(logged_in_client):  # pylint: disable=redefined-outer-name
    """GET /check_barcode_stack returns None when the stack is empty."""
    response = logged_in_client.get("/check_barcode_stack")

    assert response.status_code == 200
    assert response.json == {"barcode": None}


def test_check_pops_only_one_item(logged_in_client):  # pylint: disable=redefined-outer-name
    """Each call to /check_barcode_stack pops exactly one item."""
    config_module.BARCODE_STACK.extend(["A", "B"])

    response1 = logged_in_client.get("/check_barcode_stack")
    response2 = logged_in_client.get("/check_barcode_stack")

    assert response1.json["barcode"] == "B"
    assert response2.json["barcode"] == "A"
    assert not config_module.BARCODE_STACK


def test_check_requires_login(client):  # pylint: disable=redefined-outer-name
    """GET /check_barcode_stack without a session redirects or returns 401."""
    response = client.get("/check_barcode_stack")
    assert response.status_code in (302, 401)
