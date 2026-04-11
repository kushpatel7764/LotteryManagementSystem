# pylint: disable=redefined-outer-name
"""Tests for the check_error utility in lottery_app.utils.error_hanlder."""
from unittest.mock import Mock

import pytest

import lottery_app.utils.error_hanlder as error_utils


@pytest.fixture
def message_holder():
    """Return an empty message holder dict."""
    return {"message": "", "message_type": ""}


def test_check_error_returns_normal_result():
    """A plain non-tuple value is returned unchanged."""
    result = error_utils.check_error(42)
    assert result == 42


def test_check_error_callable_returns_value():
    """A callable is invoked and its return value is returned."""
    result = error_utils.check_error(lambda: "ok")
    assert result == "ok"


def test_check_error_tuple_unhandled_type():
    """A tuple with an unrecognised type is returned as-is."""
    result = error_utils.check_error(("msg", "info"))
    assert result == ("msg", "info")


def test_check_error_error_tuple_sets_message(message_holder):
    """An error tuple populates message_holder and returns the fallback."""
    result = error_utils.check_error(
        ("Bad things", "error"), message_holder=message_holder, fallback=False
    )

    assert result is False
    assert message_holder["message"] == "Bad things"
    assert message_holder["message_type"] == "error"


def test_warning_overwrites_success(message_holder):
    """A warning overwrites a prior success message."""
    message_holder["message_type"] = "success"

    error_utils.check_error(("Careful", "warning"), message_holder=message_holder)

    assert message_holder["message"] == "Careful"
    assert message_holder["message_type"] == "warning"


def test_warning_does_not_overwrite_error(message_holder):
    """A warning does NOT overwrite an existing error message."""
    message_holder["message"] = "Fatal"
    message_holder["message_type"] = "error"

    error_utils.check_error(("Minor", "warning"), message_holder=message_holder)

    assert message_holder["message"] == "Fatal"
    assert message_holder["message_type"] == "error"


def test_success_does_not_overwrite_warning(message_holder):
    """A success message does NOT overwrite an existing warning."""
    message_holder["message"] = "Be careful"
    message_holder["message_type"] = "warning"

    error_utils.check_error(("All good", "success"), message_holder=message_holder)

    assert message_holder["message"] == "Be careful"
    assert message_holder["message_type"] == "warning"


def test_success_does_not_overwrite_error(message_holder):
    """A success message does NOT overwrite an existing error."""
    message_holder["message"] = "Fatal"
    message_holder["message_type"] = "error"

    error_utils.check_error(("All good", "success"), message_holder=message_holder)

    assert message_holder["message"] == "Fatal"
    assert message_holder["message_type"] == "error"


def test_check_error_flashes(monkeypatch):
    """flash is called with the correct category when flash_prefix is provided."""
    flash_mock = Mock()
    monkeypatch.setattr(error_utils, "flash", flash_mock)

    error_utils.check_error(("Oops", "error"), flash_prefix="test")

    flash_mock.assert_called_once_with("Oops", "test_error")


def test_check_error_no_flash_when_not_requested(monkeypatch):
    """flash is NOT called when flash_prefix is omitted."""
    flash_mock = Mock()
    monkeypatch.setattr(error_utils, "flash", flash_mock)

    error_utils.check_error(("Oops", "error"))

    flash_mock.assert_not_called()


def test_check_error_exception_flashes(monkeypatch):
    """An exception inside a callable triggers a flash with the error details."""
    flash_mock = Mock()
    monkeypatch.setattr(error_utils, "flash", flash_mock)

    def boom():
        raise RuntimeError("explode")

    error_utils.check_error(boom, flash_prefix="db")

    flash_mock.assert_called_once()
    args, _ = flash_mock.call_args
    assert "Unexpected Error: explode" in args[0]
    assert args[1] == "db_error"
