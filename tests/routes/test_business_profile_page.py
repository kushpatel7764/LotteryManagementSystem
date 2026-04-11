"""Tests for the business profile page route and its helper functions."""
import json
from unittest.mock import patch, MagicMock, mock_open

import pytest

from lottery_app.routes.business_profile import extract_business_profile_form_data
from lottery_app.routes.business_profile import validate_and_update_business_info
from lottery_app.routes.settings import update_invoice_output_path


@pytest.fixture
def valid_data():
    """Return a dict of valid business profile form values."""
    return {
        "business_name": "Kush Shop",
        "business_address": "123 Main Street, Boston, MA 02134",
        "business_phone": "+12345678901",
        "business_email": "test@example.com",
    }


@pytest.fixture
def app_context(app):  # pylint: disable=redefined-outer-name
    """Push a request context for tests that need flash/session."""
    with app.test_request_context():
        yield


# ---------------------------------------------------
#   TESTS
# ---------------------------------------------------


def test_business_profile_requires_login(client):
    """Unauthenticated users should be redirected to login."""
    response = client.get("/business_profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_business_profile_get_authenticated(client, auth, captured_templates):
    """GET /business_profile when logged in renders the correct template."""
    auth.login()
    mock_config = {
        "business_name": "Shop A",
        "business_address": "123 Main",
        "business_phone": "555-0000",
        "business_email": "test@example.com",
    }

    mock_users = [{"id": 1, "username": "admin"}]

    with (
        patch(
            "lottery_app.routes.business_profile.load_config", return_value=mock_config
        ),
        patch(
            "lottery_app.routes.business_profile.get_all_users", return_value=mock_users
        ),
    ):
        response = client.get("/business_profile", follow_redirects=True)
        print("CAPTURED:", captured_templates)
        assert response.status_code == 200

        template, context = captured_templates[-1]
        assert template.name == "business_profile.html"
        assert context["business_Info"]["Name"] == "Shop A"
        assert context["users"] == mock_users


def test_business_profile_post_valid(client, auth, captured_templates):
    """POSTing valid data calls validate + update and re-renders the template."""
    auth.login()
    initial_config = {
        "business_name": "Old Shop",
        "business_address": "Old Addr",
        "business_phone": "000",
        "business_email": "old@example.com",
    }

    post_data = {
        "business_name": "New Shop",
        "business_address": "New Addr",
        "business_phone": "123456",
        "business_email": "new@example.com",
    }

    mock_validate = MagicMock(return_value=[])
    mock_users = [{"id": 1, "username": "admin"}]

    with (
        patch(
            "lottery_app.routes.business_profile.load_config",
            return_value=initial_config,
        ),
        patch(
            "lottery_app.routes.business_profile.extract_business_profile_form_data",
            return_value=post_data,
        ),
        patch(
            "lottery_app.routes.business_profile.validate_and_update_business_info",
            mock_validate,
        ),
        patch(
            "lottery_app.routes.business_profile.get_all_users", return_value=mock_users
        ),
    ):
        response = client.post("/business_profile", data=post_data)
        assert response.status_code == 200

        mock_validate.assert_called_once_with(post_data)

        template, _ = captured_templates[-1]
        assert template.name == "business_profile.html"


def test_business_profile_post_invalid(client, auth):
    """POST with validation errors flashes the error message."""
    auth.login()

    initial_config = {
        "business_name": "Shop",
        "business_address": "Addr",
        "business_phone": "000",
        "business_email": "old@example.com",
    }

    post_data = {"business_name": "", "business_email": "bad"}

    with (
        patch(
            "lottery_app.routes.business_profile.load_config",
            return_value=initial_config,
        ),
        patch(
            "lottery_app.routes.business_profile.extract_business_profile_form_data",
            return_value=post_data,
        ),
        patch(
            "lottery_app.routes.business_profile.validate_and_update_business_info",
            return_value=["Invalid email"],
        ),
        patch("lottery_app.routes.business_profile.get_all_users", return_value=[]),
    ):
        response = client.post(
            "/business_profile", data=post_data, follow_redirects=True
        )
        assert response.status_code == 200

        flashed = [msg for msg in response.data.split(b"\n") if b"Invalid email" in msg]
        assert flashed


def test_extract_form_data_all_fields_present(app):
    """All fields provided in request.form override config defaults."""
    test_config = {
        "business_name": "Default Shop",
        "business_address": "123 Main St",
        "business_phone": "555-0000",
        "business_email": "default@example.com",
    }

    with app.test_request_context(
        "/",
        method="POST",
        data={
            "BusinessName": "New Shop",
            "BusinessAddress": "456 Park Ave",
            "BusinessPhone": "555-1234",
            "BusinessEmail": "new@example.com",
        },
    ):
        form_data = extract_business_profile_form_data(test_config)
        assert form_data["business_name"] == "New Shop"
        assert form_data["business_address"] == "456 Park Ave"
        assert form_data["business_phone"] == "555-1234"
        assert form_data["business_email"] == "new@example.com"


def test_extract_form_data_some_fields_missing(app):
    """Missing form fields fall back to the config defaults."""
    test_config = {
        "business_name": "Default Shop",
        "business_address": "123 Main St",
        "business_phone": "555-0000",
        "business_email": "default@example.com",
    }

    with app.test_request_context(
        "/",
        method="POST",
        data={"BusinessName": "New Shop", "BusinessPhone": "555-1234"},
    ):
        form_data = extract_business_profile_form_data(test_config)
        assert form_data["business_name"] == "New Shop"
        assert form_data["business_phone"] == "555-1234"
        assert form_data["business_address"] == "123 Main St"
        assert form_data["business_email"] == "default@example.com"


def test_extract_form_data_no_fields_provided(app):
    """Empty form submission returns the config unchanged."""
    test_config = {
        "business_name": "Default Shop",
        "business_address": "123 Main St",
        "business_phone": "555-0000",
        "business_email": "default@example.com",
    }

    with app.test_request_context("/", method="POST", data={}):
        form_data = extract_business_profile_form_data(test_config)
        assert form_data == test_config


# -------------------------------
# TEST: All fields valid
# -------------------------------
@patch("lottery_app.routes.business_profile.update_business_info")
def test_all_fields_valid(mock_update, valid_data):  # pylint: disable=redefined-outer-name
    """Valid data produces no errors and calls update for every field."""
    errors = validate_and_update_business_info(valid_data)

    assert not errors
    assert mock_update.call_count == 4

    mock_update.assert_any_call(name="business_name", value="Kush Shop")
    mock_update.assert_any_call(
        name="business_address", value="123 Main Street, Boston, MA 02134"
    )
    mock_update.assert_any_call(name="business_phone", value="+12345678901")
    mock_update.assert_any_call(name="business_email", value="test@example.com")


# -------------------------------
# TEST: Invalid address
# -------------------------------
@patch("lottery_app.routes.business_profile.update_business_info")
def test_invalid_address(mock_update, valid_data):  # pylint: disable=redefined-outer-name
    """An invalid address is replaced with an empty string and reported."""
    valid_data["business_address"] = "INVALID_ADDRESS"

    errors = validate_and_update_business_info(valid_data)

    assert errors == ["Not a valid ADDRESS!"]
    mock_update.assert_any_call(name="business_address", value="")


# -------------------------------
# TEST: Invalid phone number
# -------------------------------
@patch("lottery_app.routes.business_profile.update_business_info")
def test_invalid_phone(mock_update, valid_data):  # pylint: disable=redefined-outer-name
    """A non-numeric phone number is replaced with an empty string and reported."""
    valid_data["business_phone"] = "123-abc-0000"

    errors = validate_and_update_business_info(valid_data)

    assert errors == ["Not a valid PHONE NUMBER!"]
    mock_update.assert_any_call(name="business_phone", value="")


# -------------------------------
# TEST: Invalid email
# -------------------------------
@patch("lottery_app.routes.business_profile.update_business_info")
def test_invalid_email(mock_update, valid_data):  # pylint: disable=redefined-outer-name
    """A malformed email is replaced with an empty string and reported."""
    valid_data["business_email"] = "wrong-email"

    errors = validate_and_update_business_info(valid_data)

    assert errors == ["Not a valid EMAIL!"]
    mock_update.assert_any_call(name="business_email", value="")


# -------------------------------
# TEST: Empty fields (allowed)
# -------------------------------
@patch("lottery_app.routes.business_profile.update_business_info")
def test_empty_fields_allowed(mock_update):
    """Empty field values are accepted without errors."""
    data = {
        "business_name": "",
        "business_address": "",
        "business_phone": "",
        "business_email": "",
    }

    errors = validate_and_update_business_info(data)

    assert not errors
    mock_update.assert_any_call(name="business_name", value="")
    mock_update.assert_any_call(name="business_address", value="")
    mock_update.assert_any_call(name="business_phone", value="")
    mock_update.assert_any_call(name="business_email", value="")


# -------------------------------
# TEST: Multiple invalid fields
# -------------------------------
@patch("lottery_app.routes.business_profile.update_business_info")
def test_multiple_invalid_fields(mock_update):
    """Multiple invalid fields each produce an error and are cleared."""
    data = {
        "business_name": "Shop",
        "business_address": "BAD",
        "business_phone": "NOT_NUMBERS",
        "business_email": "BAD_EMAIL",
    }

    errors = validate_and_update_business_info(data)

    assert errors == [
        "Not a valid ADDRESS!",
        "Not a valid PHONE NUMBER!",
        "Not a valid EMAIL!",
    ]

    mock_update.assert_any_call(name="business_address", value="")
    mock_update.assert_any_call(name="business_phone", value="")
    mock_update.assert_any_call(name="business_email", value="")


# -------------------------------------------
# TEST: Path changes -> must update + flash
# -------------------------------------------
@patch("lottery_app.utils.config.flash")
@patch("lottery_app.utils.config.load_config")
def test_update_output_path_changed(  # pylint: disable=redefined-outer-name
    mock_load_config, mock_flash, app_context  # pylint: disable=unused-argument
):
    """Changing the output path writes the new value and calls flash."""
    mock_load_config.return_value = {"invoice_output_path": "/old/path"}

    m = mock_open()

    with patch("builtins.open", m):
        update_invoice_output_path("/new/path")

    handle = m()
    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    written_data = json.loads(written_content)

    assert written_data["invoice_output_path"] == "/new/path"
    mock_flash.assert_called_once()


# --------------------------------------------------------
# TEST: Path stays the same -> file rewritten, no flash
# --------------------------------------------------------
@patch("lottery_app.utils.config.flash")
@patch("lottery_app.utils.config.load_config")
def test_update_output_path_same_value(  # pylint: disable=redefined-outer-name
    mock_load_config, mock_flash, app_context  # pylint: disable=unused-argument
):
    """Same-value update rewrites the file but does not call flash."""
    mock_load_config.return_value = {"invoice_output_path": "/same/path"}

    m = mock_open()

    with patch("builtins.open", m):
        update_invoice_output_path("/same/path")

    handle = m()
    written = "".join(call.args[0] for call in handle.write.call_args_list)
    written_data = json.loads(written)

    assert written_data["invoice_output_path"] == "/same/path"
    mock_flash.assert_not_called()


# ---------------------------------------------------------------
# TEST: Ensure correct JSON structure is written (regression test)
# ---------------------------------------------------------------
def patched_mock_open():
    """Return a mock_open that accumulates all write() calls."""
    m = mock_open()
    handle = m.return_value
    handle._written = ""  # pylint: disable=protected-access

    def write(data):
        handle._written += data  # pylint: disable=protected-access

    handle.write = write
    return m


@patch("lottery_app.routes.settings.flash")
@patch("lottery_app.utils.config.load_config")
def test_json_written_correctly(  # pylint: disable=redefined-outer-name
    mock_load_config,
    mock_flash,  # pylint: disable=unused-argument
    app_context,  # pylint: disable=unused-argument
):
    """The JSON file written by update_invoice_output_path has the correct structure."""
    mock_load_config.return_value = {
        "invoice_output_path": "/old/path",
        "other_setting": "unchanged",
    }

    m = patched_mock_open()

    with patch("builtins.open", m):
        update_invoice_output_path("/abc/xyz")

    written_data = json.loads(m.return_value._written)  # pylint: disable=protected-access

    assert written_data == {
        "invoice_output_path": "/abc/xyz",
        "other_setting": "unchanged",
    }
