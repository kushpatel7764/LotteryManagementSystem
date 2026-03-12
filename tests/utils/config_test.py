import pytest
from lottery_app.utils.config import (
    update_ticket_order,
    update_invoice_output_path,
    update_should_poll,
)
import json
from unittest.mock import mock_open

import lottery_app.utils.config as config_utils


# ============================================================
# update_ticket_order tests
# ============================================================
def test_update_ticket_order_updates_and_flashes(update_env, json_assert):
    initial = {"ticket_order": ["A", "B"]}
    load_cfg, flash_mock, m = update_env(initial)

    update_ticket_order(["C", "D"])

    json_assert(m, {"ticket_order": ["C", "D"]})
    flash_mock.assert_called_once_with(
        "Ticket Order Updated to ['C', 'D'] sucessfully.", "settings_success"
    )

def test_update_ticket_order_no_change_no_flash(update_env, json_assert):
    initial = {"ticket_order": ["X", "Y"]}
    load_cfg, flash_mock, m = update_env(initial)

    update_ticket_order(["X", "Y"])

    # Should still write the file but not flash
    json_assert(m, {"ticket_order": ["X", "Y"]})
    flash_mock.assert_not_called()

def test_update_ticket_order_invalid_type(update_env):
    initial = {"ticket_order": ["A"]}
    update_env(initial)

    with pytest.raises(TypeError):
        update_ticket_order("not a list")  # should raise


# ============================================================
# update_invoice_output_path tests
# ============================================================
def test_update_invoice_output_path_updates_and_flashes(update_env, json_assert):
    initial = {"invoice_output_path": "/old"}
    load_cfg, flash_mock, m = update_env(initial)

    update_invoice_output_path("/new")

    json_assert(m, {"invoice_output_path": "/new"})
    flash_mock.assert_called_once()
    args, kwargs = flash_mock.call_args
    assert "Updated" in args[0] or "updated" in args[0]

def test_update_invoice_output_path_no_change_no_flash(update_env, json_assert):
    initial = {"invoice_output_path": "/same"}
    load_cfg, flash_mock, m = update_env(initial)

    update_invoice_output_path("/same")

    json_assert(m, {"invoice_output_path": "/same"})
    flash_mock.assert_not_called()

def test_update_invoice_output_path_invalid_type(update_env):
    initial = {"invoice_output_path": "/old"}
    update_env(initial)

    with pytest.raises(TypeError) as e:
        update_invoice_output_path(123)  # expecting string

    assert "string" in str(e.value).lower()


# ============================================================
# update_should_poll tests
# ============================================================
def test_update_should_poll_updates(update_env, json_assert):
    initial = {"should_poll": "false"}
    load_cfg, flash_mock, m = update_env(initial)

    update_should_poll("true")

    json_assert(m, {"should_poll": "true"})
    # Does not flash, so:
    flash_mock.assert_not_called()

def test_update_should_poll_invalid_type(update_env):
    initial = {"should_poll": "false"}
    update_env(initial)

    with pytest.raises(TypeError):
        update_should_poll(True)  # expecting string
        
        

# ============================================================
# update_business_info tests
# ============================================================
@pytest.fixture
def sample_config():
    return {
        "business_name": "Old Name",
        "business_email": "old@email.com"
    }


def test_update_business_info_raises_type_error(sample_config, monkeypatch):
    monkeypatch.setattr(
        config_utils,
        "load_config",
        lambda: sample_config.copy()
    )

    with pytest.raises(TypeError):
        config_utils.update_business_info("business_name", 123)

def test_update_business_info_success(sample_config, monkeypatch):
    # Mock load_config
    monkeypatch.setattr(
        config_utils,
        "load_config",
        lambda: sample_config.copy()
    )

    # Mock CONFIG_PATH
    monkeypatch.setattr(config_utils, "CONFIG_PATH", "fake_config.json")

    # Mock open()
    m = mock_open()
    monkeypatch.setattr("builtins.open", m)

    # Capture flash calls
    flashed = {}

    def fake_flash(message, category):
        flashed["message"] = message
        flashed["category"] = category

    monkeypatch.setattr(config_utils, "flash", fake_flash)

    config_utils.update_business_info("business_name", "New Name")

    # File was written
    m.assert_called_once_with("fake_config.json", "w", encoding="utf-8")

    # Flash was triggered
    assert flashed["category"] == "business-profile_success"
    assert "business_name is updated to New Name successfully." in flashed["message"]


def test_update_business_info_no_change_no_flash(sample_config, monkeypatch):
    monkeypatch.setattr(
        config_utils,
        "load_config",
        lambda: sample_config.copy()
    )

    monkeypatch.setattr(config_utils, "CONFIG_PATH", "fake_config.json")

    m = mock_open()
    monkeypatch.setattr("builtins.open", m)

    flash_called = False

    def fake_flash(*args, **kwargs):
        nonlocal flash_called
        flash_called = True

    monkeypatch.setattr(config_utils, "flash", fake_flash)

    config_utils.update_business_info("business_name", "Old Name")

    assert flash_called is False


def test_update_business_info_empty_string_no_flash(sample_config, monkeypatch):
    monkeypatch.setattr(
        config_utils,
        "load_config",
        lambda: sample_config.copy()
    )

    monkeypatch.setattr(config_utils, "CONFIG_PATH", "fake_config.json")

    m = mock_open()
    monkeypatch.setattr("builtins.open", m)

    flash_called = False

    def fake_flash(*args, **kwargs):
        nonlocal flash_called
        flash_called = True

    monkeypatch.setattr(config_utils, "flash", fake_flash)

    config_utils.update_business_info("business_name", "")

    assert flash_called is False

def test_update_business_info_writes_updated_config(sample_config, monkeypatch):
    monkeypatch.setattr(
        config_utils,
        "load_config",
        lambda: sample_config.copy()
    )

    monkeypatch.setattr(config_utils, "CONFIG_PATH", "fake_config.json")

    m = mock_open()
    monkeypatch.setattr("builtins.open", m)

    monkeypatch.setattr(config_utils, "flash", lambda *args, **kwargs: None)

    config_utils.update_business_info("business_email", "new@email.com")

    # Grab written JSON
    written = m().write.call_args_list
    written_json = "".join(call.args[0] for call in written)

    data = json.loads(written_json)
    assert data["business_email"] == "new@email.com"
