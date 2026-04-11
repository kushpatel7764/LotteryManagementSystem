# pylint: disable=redefined-outer-name
"""Tests for config update utilities in lottery_app.utils.config."""
import json
from unittest.mock import mock_open

import pytest

import lottery_app.utils.config as config_utils
from lottery_app.utils.config import (
    update_ticket_order,
    update_invoice_output_path,
    update_should_poll,
)


# ============================================================
# update_ticket_order tests
# ============================================================
def test_update_ticket_order_updates_and_flashes(update_env, json_assert):
    """Changing ticket order writes the new value and flashes a success message."""
    initial = {"ticket_order": ["A", "B"]}
    _, flash_mock, m = update_env(initial)

    update_ticket_order(["C", "D"])

    json_assert(m, {"ticket_order": ["C", "D"]})
    flash_mock.assert_called_once_with(
        "Ticket Order Updated to ['C', 'D'] sucessfully.", "settings_success"
    )


def test_update_ticket_order_no_change_no_flash(update_env, json_assert):
    """Setting the same ticket order writes the file but does not flash."""
    initial = {"ticket_order": ["X", "Y"]}
    _, flash_mock, m = update_env(initial)

    update_ticket_order(["X", "Y"])

    json_assert(m, {"ticket_order": ["X", "Y"]})
    flash_mock.assert_not_called()


def test_update_ticket_order_invalid_type(update_env):
    """Passing a non-list raises TypeError."""
    initial = {"ticket_order": ["A"]}
    update_env(initial)

    with pytest.raises(TypeError):
        update_ticket_order("not a list")


# ============================================================
# update_invoice_output_path tests
# ============================================================
def test_update_invoice_output_path_updates_and_flashes(update_env, json_assert):
    """Changing the output path writes the new value and flashes a success message."""
    initial = {"invoice_output_path": "/old"}
    _, flash_mock, m = update_env(initial)

    update_invoice_output_path("/new")

    json_assert(m, {"invoice_output_path": "/new"})
    flash_mock.assert_called_once()
    args, _ = flash_mock.call_args
    assert "Updated" in args[0] or "updated" in args[0]


def test_update_invoice_output_path_no_change_no_flash(update_env, json_assert):
    """Setting the same output path writes the file but does not flash."""
    initial = {"invoice_output_path": "/same"}
    _, flash_mock, m = update_env(initial)

    update_invoice_output_path("/same")

    json_assert(m, {"invoice_output_path": "/same"})
    flash_mock.assert_not_called()


def test_update_invoice_output_path_invalid_type(update_env):
    """Passing a non-string raises TypeError with 'string' in the message."""
    initial = {"invoice_output_path": "/old"}
    update_env(initial)

    with pytest.raises(TypeError) as e:
        update_invoice_output_path(123)

    assert "string" in str(e.value).lower()


# ============================================================
# update_should_poll tests
# ============================================================
def test_update_should_poll_updates(update_env, json_assert):
    """Changing should_poll writes the new value without flashing."""
    initial = {"should_poll": "false"}
    _, flash_mock, m = update_env(initial)

    update_should_poll("true")

    json_assert(m, {"should_poll": "true"})
    flash_mock.assert_not_called()


def test_update_should_poll_invalid_type(update_env):
    """Passing a boolean instead of a string raises TypeError."""
    initial = {"should_poll": "false"}
    update_env(initial)

    with pytest.raises(TypeError):
        update_should_poll(True)


# ============================================================
# update_business_info tests
# ============================================================
@pytest.fixture
def sample_config():
    """Return a sample config dict for business_info tests."""
    return {"business_name": "Old Name", "business_email": "old@email.com"}


def test_update_business_info_raises_type_error(sample_config, monkeypatch):
    """Passing a non-string value raises TypeError."""
    monkeypatch.setattr(config_utils, "load_config", sample_config.copy)

    with pytest.raises(TypeError):
        config_utils.update_business_info("business_name", 123)


def test_update_business_info_success(sample_config, monkeypatch):
    """A valid update writes the config file and flashes a success message."""
    monkeypatch.setattr(config_utils, "load_config", sample_config.copy)
    monkeypatch.setattr(config_utils, "CONFIG_PATH", "fake_config.json")

    m = mock_open()
    monkeypatch.setattr("builtins.open", m)

    flashed = {}

    def fake_flash(message, category):
        flashed["message"] = message
        flashed["category"] = category

    monkeypatch.setattr(config_utils, "flash", fake_flash)

    config_utils.update_business_info("business_name", "New Name")

    m.assert_called_once_with("fake_config.json", "w", encoding="utf-8")
    assert flashed["category"] == "business-profile_success"
    assert "business_name is updated to New Name successfully." in flashed["message"]


def test_update_business_info_no_change_no_flash(sample_config, monkeypatch):
    """Setting the same value writes the file but does not flash."""
    monkeypatch.setattr(config_utils, "load_config", sample_config.copy)
    monkeypatch.setattr(config_utils, "CONFIG_PATH", "fake_config.json")

    m = mock_open()
    monkeypatch.setattr("builtins.open", m)

    flash_called = False

    def fake_flash(*_args, **_kwargs):
        nonlocal flash_called
        flash_called = True

    monkeypatch.setattr(config_utils, "flash", fake_flash)

    config_utils.update_business_info("business_name", "Old Name")

    assert flash_called is False


def test_update_business_info_empty_string_no_flash(sample_config, monkeypatch):
    """Setting a field to an empty string writes the file but does not flash."""
    monkeypatch.setattr(config_utils, "load_config", sample_config.copy)
    monkeypatch.setattr(config_utils, "CONFIG_PATH", "fake_config.json")

    m = mock_open()
    monkeypatch.setattr("builtins.open", m)

    flash_called = False

    def fake_flash(*_args, **_kwargs):
        nonlocal flash_called
        flash_called = True

    monkeypatch.setattr(config_utils, "flash", fake_flash)

    config_utils.update_business_info("business_name", "")

    assert flash_called is False


def test_update_business_info_writes_updated_config(sample_config, monkeypatch):
    """The updated config key is present in the JSON written to disk."""
    monkeypatch.setattr(config_utils, "load_config", sample_config.copy)
    monkeypatch.setattr(config_utils, "CONFIG_PATH", "fake_config.json")

    m = mock_open()
    monkeypatch.setattr("builtins.open", m)
    monkeypatch.setattr(config_utils, "flash", lambda *args, **kwargs: None)

    config_utils.update_business_info("business_email", "new@email.com")

    written = m().write.call_args_list
    written_json = "".join(call.args[0] for call in written)

    data = json.loads(written_json)
    assert data["business_email"] == "new@email.com"
