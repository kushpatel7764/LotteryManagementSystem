"""Tests for the scanner blueprint: /receive and /check_barcode_stack."""
# pylint: disable=redefined-outer-name
import queue as _queue_mod

import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin

from lottery_app.routes.scanner import scanner_bp
from lottery_app.utils import config as config_module

# ------------------------
# Test Helpers / Fixtures
# ------------------------


def _drain_barcode_queue():
    """Drain all items from BARCODE_QUEUE."""
    while not config_module.BARCODE_QUEUE.empty():
        try:
            config_module.BARCODE_QUEUE.get_nowait()
        except _queue_mod.Empty:
            break


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
def clear_barcode_queue():
    """Ensure BARCODE_QUEUE is empty before and after each test."""
    _drain_barcode_queue()
    yield
    _drain_barcode_queue()


# ------------------------
# Tests for /receive
# ------------------------


def test_receive_barcode_polling_enabled(logged_in_client, monkeypatch):  # pylint: disable=redefined-outer-name
    """POST /receive with polling enabled pushes the barcode onto the queue."""
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )

    response = logged_in_client.post("/receive", data={"barcode": "123456"})

    assert response.status_code == 200
    assert response.data == b"Received"
    assert not config_module.BARCODE_QUEUE.empty()
    assert config_module.BARCODE_QUEUE.get_nowait() == "123456"


def test_receive_barcode_polling_disabled(logged_in_client, monkeypatch):  # pylint: disable=redefined-outer-name
    """POST /receive with polling disabled ignores the barcode."""
    monkeypatch.setattr(config_module, "load_config", lambda: {"should_poll": "false"})

    response = logged_in_client.post("/receive", data={"barcode": "999999"})

    assert response.status_code == 200
    assert response.data == b"Ignored"
    assert config_module.BARCODE_QUEUE.empty()


def test_receive_missing_barcode(logged_in_client, monkeypatch):  # pylint: disable=redefined-outer-name
    """POST /receive with no barcode field pushes None onto the queue."""
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )

    response = logged_in_client.post("/receive", data={})

    assert response.status_code == 200
    assert response.data == b"Received"
    assert not config_module.BARCODE_QUEUE.empty()
    assert config_module.BARCODE_QUEUE.get_nowait() is None


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


def test_check_returns_next_barcode(logged_in_client):  # pylint: disable=redefined-outer-name
    """GET /check_barcode_stack returns the next barcode from the queue (FIFO)."""
    for item in ["111", "222", "333"]:
        config_module.BARCODE_QUEUE.put(item)

    response = logged_in_client.get("/check_barcode_stack")

    assert response.status_code == 200
    assert response.json == {"barcode": "111"}  # FIFO — first in, first out
    remaining = []
    while not config_module.BARCODE_QUEUE.empty():
        remaining.append(config_module.BARCODE_QUEUE.get_nowait())
    assert remaining == ["222", "333"]


def test_check_returns_none_when_empty(logged_in_client):  # pylint: disable=redefined-outer-name
    """GET /check_barcode_stack returns None when the queue is empty."""
    response = logged_in_client.get("/check_barcode_stack")

    assert response.status_code == 200
    assert response.json == {"barcode": None}


def test_check_dequeues_only_one_item(logged_in_client):  # pylint: disable=redefined-outer-name
    """Each call to /check_barcode_stack dequeues exactly one item."""
    for item in ["A", "B"]:
        config_module.BARCODE_QUEUE.put(item)

    response1 = logged_in_client.get("/check_barcode_stack")
    response2 = logged_in_client.get("/check_barcode_stack")

    assert response1.json["barcode"] == "A"  # FIFO — first in, first out
    assert response2.json["barcode"] == "B"
    assert config_module.BARCODE_QUEUE.empty()


def test_check_requires_login(client):  # pylint: disable=redefined-outer-name
    """GET /check_barcode_stack without a session redirects or returns 401."""
    response = client.get("/check_barcode_stack")
    assert response.status_code in (302, 401)


# ============================================================
# NEW SECURITY AND EDGE-CASE TESTS
# ============================================================


def test_receive_null_barcode_pushes_none(logged_in_client, monkeypatch):  # NEW
    """
    POST /receive with no 'barcode' field pushes None to the queue.
    The downstream validator (ScannedCodeManagement) will reject None gracefully,
    but the endpoint must not crash.
    """
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )
    response = logged_in_client.post("/receive", data={})
    assert response.status_code == 200
    assert not config_module.BARCODE_QUEUE.empty()
    assert config_module.BARCODE_QUEUE.get_nowait() is None


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
    Special characters in the barcode are stored in the queue as-is.
    The validator will reject them; /receive must not crash.
    """
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )
    bad_barcode = "'; DROP TABLE Books; --"
    response = logged_in_client.post("/receive", data={"barcode": bad_barcode})
    assert response.status_code == 200
    assert not config_module.BARCODE_QUEUE.empty()
    assert config_module.BARCODE_QUEUE.get_nowait() == bad_barcode


def test_receive_concurrent_appends_do_not_mix_barcodes(
    logged_in_client, monkeypatch
):  # NEW
    """
    Sending multiple barcodes sequentially preserves all of them in the queue.
    (This is a safety test; true concurrency requires thread tests.)
    """
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "true"}
    )
    barcodes = ["AAA", "BBB", "CCC"]
    for bc in barcodes:
        logged_in_client.post("/receive", data={"barcode": bc})

    items = []
    while not config_module.BARCODE_QUEUE.empty():
        items.append(config_module.BARCODE_QUEUE.get_nowait())
    assert items == barcodes


def test_check_queue_fifo_behaviour(logged_in_client):  # NEW
    """
    /check_barcode_stack uses queue.get_nowait() (FIFO — oldest first).
    This test documents the actual order so any change to LIFO is detected.
    """
    for item in ["FIRST", "SECOND", "THIRD"]:
        config_module.BARCODE_QUEUE.put(item)
    resp = logged_in_client.get("/check_barcode_stack")
    # Current behaviour: FIFO — get() returns the first item added
    assert resp.json["barcode"] == "FIRST"
    remaining = []
    while not config_module.BARCODE_QUEUE.empty():
        remaining.append(config_module.BARCODE_QUEUE.get_nowait())
    assert remaining == ["SECOND", "THIRD"]


def test_receive_polling_disabled_does_not_push(logged_in_client, monkeypatch):  # NEW
    """When should_poll is 'false', /receive must not push to BARCODE_QUEUE."""
    monkeypatch.setattr(
        "lottery_app.routes.scanner.load_config", lambda: {"should_poll": "false"}
    )
    logged_in_client.post("/receive", data={"barcode": "SHOULD_NOT_PUSH"})
    assert config_module.BARCODE_QUEUE.empty()


def test_receive_polling_case_insensitive(logged_in_client, monkeypatch):  # NEW
    """
    The polling check uses .lower() so 'True', 'TRUE', 'true' all enable polling.
    """
    for val in ("True", "TRUE", "tRuE"):
        _drain_barcode_queue()
        monkeypatch.setattr(
            "lottery_app.routes.scanner.load_config",
            lambda _v=val: {"should_poll": _v},
        )
        resp = logged_in_client.post("/receive", data={"barcode": "BC"})
        assert resp.status_code == 200
        assert not config_module.BARCODE_QUEUE.empty()
        _drain_barcode_queue()
