import pytest
from unittest.mock import Mock

import lottery_app.utils.error_hanlder as error_utils


# Helper fixture: empty message holder
@pytest.fixture
def message_holder():
    return {"message": "", "message_type": ""}


# Test: returns normal result (non-tuple)
def test_check_error_returns_normal_result():
    result = error_utils.check_error(42)
    assert result == 42


# Test: callable returning normal result
def test_check_error_callable_returns_value():
    result = error_utils.check_error(lambda: "ok")
    assert result == "ok"


# Test: tuple with non-handled type → return tuple
def test_check_error_tuple_unhandled_type():
    result = error_utils.check_error(("msg", "info"))
    assert result == ("msg", "info")


# Test: error tuple populates message_holder and returns fallback
def test_check_error_error_tuple_sets_message(message_holder):
    result = error_utils.check_error(
        ("Bad things", "error"), message_holder=message_holder, fallback=False
    )

    assert result is False
    assert message_holder["message"] == "Bad things"
    assert message_holder["message_type"] == "error"


# Test: warning overwrites success but not error
def test_warning_overwrites_success(message_holder):
    message_holder["message_type"] = "success"

    error_utils.check_error(("Careful", "warning"), message_holder=message_holder)

    assert message_holder["message"] == "Careful"
    assert message_holder["message_type"] == "warning"


# Test: warning does NOT overwrite error
def test_warning_does_not_overwrite_error(message_holder):
    message_holder["message"] = "Fatal"
    message_holder["message_type"] = "error"

    error_utils.check_error(("Minor", "warning"), message_holder=message_holder)

    assert message_holder["message"] == "Fatal"
    assert message_holder["message_type"] == "error"


# Test: success does NOT overwrite warning
def test_success_does_not_overwrite_warning(message_holder):
    message_holder["message"] = "Be careful"
    message_holder["message_type"] = "warning"

    error_utils.check_error(("All good", "success"), message_holder=message_holder)

    assert message_holder["message"] == "Be careful"
    assert message_holder["message_type"] == "warning"


# Test: success does NOT overwrite error
def test_success_does_not_overwrite_error(message_holder):
    message_holder["message"] = "Fatal"
    message_holder["message_type"] = "error"

    error_utils.check_error(("All good", "success"), message_holder=message_holder)

    assert message_holder["message"] == "Fatal"
    assert message_holder["message_type"] == "error"


# Test: flash is called when flash_prefix provided
def test_check_error_flashes(monkeypatch):
    flash_mock = Mock()
    monkeypatch.setattr(error_utils, "flash", flash_mock)

    error_utils.check_error(("Oops", "error"), flash_prefix="test")

    flash_mock.assert_called_once_with("Oops", "test_error")


# Test: no flash when flash_prefix is None
def test_check_error_no_flash_when_not_requested(monkeypatch):
    flash_mock = Mock()
    monkeypatch.setattr(error_utils, "flash", flash_mock)

    error_utils.check_error(("Oops", "error"))

    flash_mock.assert_not_called()


# Test: no flash when flash_prefix is None
def test_check_error_no_flash_when_not_requested(monkeypatch):
    flash_mock = Mock()
    monkeypatch.setattr(error_utils, "flash", flash_mock)

    error_utils.check_error(("Oops", "error"))

    flash_mock.assert_not_called()


# Test: exception triggers flash
def test_check_error_exception_flashes(monkeypatch):
    flash_mock = Mock()
    monkeypatch.setattr(error_utils, "flash", flash_mock)

    def boom():
        raise RuntimeError("explode")

    error_utils.check_error(boom, flash_prefix="db")

    flash_mock.assert_called_once()
    args, _ = flash_mock.call_args
    assert "Unexpected Error: explode" in args[0]
    assert args[1] == "db_error"
