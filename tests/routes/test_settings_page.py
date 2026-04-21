"""Tests for the settings page route and its helper functions."""
from unittest.mock import patch

import pytest

from lottery_app.routes.settings import (
    extract_setting_form_data,
    validate_invoice_output_path,
)


# -------------------------------------------------------------------------
# extract_setting_form_data tests
# -------------------------------------------------------------------------
def test_extract_setting_form_data_with_post_request(app):
    """Ensure form fields override config defaults."""
    config = {
        "ticket_order": "asc",
        "invoice_output_path": "/default/path",
        "should_poll": "false",
    }

    with app.test_request_context(
        "/settings",
        method="POST",
        data={
            "ticket_order": "desc",
            "outputPath": "/new/output",
            "polling_state": "true",
        },
    ):
        result = extract_setting_form_data(config)

    assert result["ticket_order"] == "desc"
    assert result["output_path"] == "/new/output"
    assert result["should_poll"] == "true"


def test_extract_setting_form_data_fallbacks(app):
    """Ensure missing form data falls back to config values."""
    config = {
        "ticket_order": "asc",
        "invoice_output_path": "/fallback/path",
        "should_poll": "false",
    }

    with app.test_request_context("/settings", method="POST", data={}):
        result = extract_setting_form_data(config)

    assert result["ticket_order"] == "asc"
    assert result["output_path"] == "/fallback/path"
    assert result["should_poll"] == "false"


# -------------------------------------------------------------------------
# validate_invoice_output_path tests
# -------------------------------------------------------------------------
def test_validate_invoice_output_path_valid(tmp_path, monkeypatch):
    """If the directory exists inside the (mocked) home, return it with no warning."""
    real_dir = tmp_path / "out"
    real_dir.mkdir()

    monkeypatch.setattr("lottery_app.routes.settings.Path.home", staticmethod(lambda: tmp_path))

    valid_path, warning = validate_invoice_output_path(str(real_dir))
    assert valid_path == str(real_dir)
    assert warning is None


@patch("lottery_app.routes.settings.DEFAULT_DOWNLOADS_PATH", "/fallback/downloads")
def test_validate_invoice_output_path_invalid_returns_default():
    """If invalid, returns DEFAULT_DOWNLOADS_PATH + warning."""
    valid_path, warning = validate_invoice_output_path("/not/a/real/dir")

    assert valid_path == "/fallback/downloads"
    assert "within your home" in warning.lower()


# -------------------------------------------------------------------------
# GET /settings route
# -------------------------------------------------------------------------
@patch("lottery_app.routes.settings.load_config")
def test_settings_get_route(load_config_mock, auth, client, captured_templates):  # pylint: disable=redefined-outer-name
    """GET /settings renders settings.html with the correct context."""
    auth.login()
    load_config_mock.return_value = {
        "ticket_order": "asc",
        "invoice_output_path": "/path/here",
        "should_poll": "true",
    }

    response = client.get("/settings")

    assert response.status_code == 200

    template, context = captured_templates[-1]
    assert template.name == "settings.html"
    assert context["counting_order"] == "asc"
    assert context["invoice_output_path"] == "/path/here"
    assert context["should_poll"] == "true"


# -------------------------------------------------------------------------
# POST /settings route
# -------------------------------------------------------------------------
@pytest.mark.parametrize("valid_dir", [True, False])
@patch("lottery_app.routes.settings.update_should_poll")
@patch("lottery_app.routes.settings.update_invoice_output_path")
@patch("lottery_app.routes.settings.update_ticket_order")
@patch("lottery_app.routes.settings.validate_invoice_output_path")
@patch("lottery_app.routes.settings.load_config")
def test_settings_post_route(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    load_config_mock,
    validate_mock,
    update_order_mock,
    update_path_mock,
    update_poll_mock,
    auth,
    client,
    valid_dir,
):
    """
    Tests full POST logic:
    - extract form data
    - update ticket order
    - validate + update output path
    - update should_poll
    - flash warnings if needed
    """
    auth.login()
    load_config_mock.return_value = {
        "ticket_order": "asc",
        "invoice_output_path": "/old/path",
        "should_poll": "false",
    }

    if valid_dir:
        validate_mock.return_value = ("/valid/path", None)
    else:
        validate_mock.return_value = ("/fallback/path", "Resetting to DEFAULT")

    response = client.post(
        "/settings",
        data={
            "ticket_order": "desc",
            "outputPath": "/requested/path",
            "polling_state": "true",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    update_order_mock.assert_called_once_with("desc")
    validate_mock.assert_called_once_with("/requested/path")

    if valid_dir:
        update_path_mock.assert_called_once_with("/valid/path")
    else:
        update_path_mock.assert_called_once_with("/fallback/path")

    update_poll_mock.assert_called_once_with("true")

    if valid_dir:
        assert b"DEFAULT" not in response.data
    else:
        assert b"Resetting to DEFAULT" in response.data
