import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin

from lottery_app.routes.scanner import scanner_bp
from lottery_app.utils import config as config_module


# ------------------------
# Test Helpers / Fixtures
# ------------------------

class TestUser(UserMixin):
    id = 1


@pytest.fixture
def app(monkeypatch):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return TestUser()

    app.register_blueprint(scanner_bp)

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    """
    Logs in a fake user for login_required routes.
    """
    with client.session_transaction() as session:
        session["_user_id"] = "1"
        session["_fresh"] = True
    return client


@pytest.fixture(autouse=True)
def clear_barcode_stack():
    """
    Ensure BARCODE_STACK is clean before each test.
    """
    config_module.BARCODE_STACK.clear()
    yield
    config_module.BARCODE_STACK.clear()


# ------------------------
# Tests for /receive
# ------------------------

def test_receive_barcode_polling_enabled(logged_in_client, monkeypatch):
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config",
        lambda: {"should_poll": "true"}
    )

    response = logged_in_client.post(
        "/receive",
        data={"barcode": "123456"}
    )

    assert response.status_code == 200
    assert response.data == b"Received"
    assert config_module.BARCODE_STACK == ["123456"]


def test_receive_barcode_polling_disabled(logged_in_client, monkeypatch):
    monkeypatch.setattr(
        config_module,
        "load_config",
        lambda: {"should_poll": "false"}
    )

    response = logged_in_client.post(
        "/receive",
        data={"barcode": "999999"}
    )

    assert response.status_code == 200
    assert response.data == b"Ignored"
    assert config_module.BARCODE_STACK == []


def test_receive_missing_barcode(logged_in_client, monkeypatch):
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config",
        lambda: {"should_poll": "true"}
    )

    response = logged_in_client.post("/receive", data={})

    assert response.status_code == 200
    assert response.data == b"Received"
    assert config_module.BARCODE_STACK == [None]


def test_receive_requires_login(client):
    response = client.post(
        "/receive",
        data={"barcode": "123"}
    )

    assert response.status_code in (302, 401)


# ------------------------
# Tests for /check_barcode_stack
# ------------------------

def test_check_returns_latest_barcode(logged_in_client):
    config_module.BARCODE_STACK.extend(["111", "222", "333"])

    response = logged_in_client.get("/check_barcode_stack")

    assert response.status_code == 200
    assert response.json == {"barcode": "333"}
    assert config_module.BARCODE_STACK == ["111", "222"]


def test_check_returns_none_when_empty(logged_in_client):
    response = logged_in_client.get("/check_barcode_stack")

    assert response.status_code == 200
    assert response.json == {"barcode": None}


def test_check_pops_only_one_item(logged_in_client):
    config_module.BARCODE_STACK.extend(["A", "B"])

    response1 = logged_in_client.get("/check_barcode_stack")
    response2 = logged_in_client.get("/check_barcode_stack")

    assert response1.json["barcode"] == "B"
    assert response2.json["barcode"] == "A"
    assert config_module.BARCODE_STACK == []


def test_check_requires_login(client):
    response = client.get("/check_barcode_stack")
    assert response.status_code in (302, 401)
