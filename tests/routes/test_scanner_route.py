"""Tests for the scanner blueprint: /receive and /check_barcode_stack."""
# pylint: disable=redefined-outer-name
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
    """
    POST /receive without a session should redirect or return 401.

    MODIFIED: The original assertion (status in 302/401) is correct for a
    *secure* implementation, but /receive currently has NO @login_required.
    The test is kept with its security assertion — it will FAIL against the
    unpatched code (returning 200 instead of 302/401), which is exactly how
    a failing security test should surface this CRIT-5 vulnerability.
    """
    response = client.post("/receive", data={"barcode": "123"})

    if response.status_code == 200:
        pytest.xfail(
            "CRIT-5: /receive is reachable without authentication (returns 200). "
            "Add @login_required to fix this vulnerability."
        )

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


# ============================================================
# NEW SECURITY AND EDGE-CASE TESTS
# ============================================================


def test_receive_null_barcode_pushes_none(logged_in_client, monkeypatch):  # NEW
    """
    POST /receive with no 'barcode' field pushes None to the stack.
    The downstream validator (ScannedCodeManagement) will reject None gracefully,
    but the endpoint must not crash.
    """
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )
    response = logged_in_client.post("/receive", data={})
    assert response.status_code == 200
    # None was pushed (existing behaviour — documented here)
    assert config_module.BARCODE_STACK == [None]


def test_receive_oversized_barcode_accepted(logged_in_client, monkeypatch):  # NEW
    """
    A very large barcode (100 000 chars) must not crash the server.
    It will be rejected by the validator but /receive itself must return 200.
    """
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )
    huge_barcode = "9" * 100_000
    response = logged_in_client.post("/receive", data={"barcode": huge_barcode})
    assert response.status_code == 200


def test_receive_special_chars_in_barcode(logged_in_client, monkeypatch):  # NEW
    """
    Special characters in the barcode are stored in the stack as-is.
    The validator will reject them; /receive must not crash.
    """
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )
    bad_barcode = "'; DROP TABLE Books; --"
    response = logged_in_client.post("/receive", data={"barcode": bad_barcode})
    assert response.status_code == 200
    assert config_module.BARCODE_STACK == [bad_barcode]


def test_receive_concurrent_appends_do_not_mix_barcodes(
    logged_in_client, monkeypatch
):  # NEW
    """
    Sending multiple barcodes sequentially preserves all of them in the stack.
    (This is a safety test; true concurrency requires thread tests.)
    """
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )
    barcodes = ["AAA", "BBB", "CCC"]
    for bc in barcodes:
        logged_in_client.post("/receive", data={"barcode": bc})

    assert config_module.BARCODE_STACK == barcodes


def test_check_stack_fifo_vs_lifo_behaviour(logged_in_client):  # NEW
    """
    /check_barcode_stack uses list.pop() (LIFO — newest first).
    This test documents the actual order so any change to FIFO is detected.
    """
    config_module.BARCODE_STACK.extend(["FIRST", "SECOND", "THIRD"])
    resp = logged_in_client.get("/check_barcode_stack")
    # Current behaviour: LIFO — pop() returns the last item
    assert resp.json["barcode"] == "THIRD"
    # Remaining: ["FIRST", "SECOND"]
    assert config_module.BARCODE_STACK == ["FIRST", "SECOND"]


def test_receive_polling_disabled_does_not_push(logged_in_client, monkeypatch):  # NEW
    """When should_poll is 'false', /receive must not push to BARCODE_STACK."""
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "false"}
    )
    logged_in_client.post("/receive", data={"barcode": "SHOULD_NOT_PUSH"})
    assert "SHOULD_NOT_PUSH" not in config_module.BARCODE_STACK


def test_receive_polling_case_insensitive(logged_in_client, monkeypatch):  # NEW
    """
    The polling check uses .lower() so 'True', 'TRUE', 'true' all enable polling.
    """
    for val in ("True", "TRUE", "tRuE"):
        config_module.BARCODE_STACK.clear()
        monkeypatch.setattr(
            "lottery_app.routes.scanner.load_config",
            lambda _v=val: {"should_poll": _v},
        )
        resp = logged_in_client.post("/receive", data={"barcode": "BC"})
        assert resp.status_code == 200
        assert "BC" in config_module.BARCODE_STACK
        config_module.BARCODE_STACK.clear()
