import sys
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from lottery_app.utils.version_check import (
    check_for_updates,
    auto_update,
    restart_app,
)

@pytest.fixture
def mock_app():
    app = MagicMock()
    app.logger = MagicMock()
    return app

# Tests: check_for_updates
# Update available → auto_update succeeds → restart called
@patch("lottery_app.utils.version_check.restart_app")
@patch("lottery_app.utils.version_check.auto_update")
@patch("lottery_app.utils.version_check.flash")
@patch("lottery_app.utils.version_check.requests.get")
@patch("lottery_app.utils.version_check.__version__", "1.0.0")
def test_check_for_updates_new_version_success(
    mock_get,
    mock_flash,
    mock_auto_update,
    mock_restart,
    mock_app,
):
    mock_get.return_value.json.return_value = {
        "info": {"version": "1.1.0"}
    }
    mock_auto_update.return_value = True

    check_for_updates(mock_app, "lottery_app")

    mock_flash.assert_any_call(
        "New version 1.1.0 available! Updating from 1.0.0 ...",
        "warning",
    )
    mock_flash.assert_any_call(
        "Update complete! Restarting app...",
        "success",
    )
    mock_auto_update.assert_called_once()
    mock_restart.assert_called_once_with(mock_app)

# Update available → auto_update fails → no restart
@patch("lottery_app.utils.version_check.restart_app")
@patch("lottery_app.utils.version_check.auto_update")
@patch("lottery_app.utils.version_check.flash")
@patch("lottery_app.utils.version_check.requests.get")
@patch("lottery_app.utils.version_check.__version__", "1.0.0")
def test_check_for_updates_new_version_failure(
    mock_get,
    mock_flash,
    mock_auto_update,
    mock_restart,
    mock_app,
):
    mock_get.return_value.json.return_value = {
        "info": {"version": "2.0.0"}
    }
    mock_auto_update.return_value = False

    check_for_updates(mock_app, "lottery_app")

    mock_auto_update.assert_called_once()
    mock_restart.assert_not_called()

# No update available
@patch("lottery_app.utils.version_check.auto_update")
@patch("lottery_app.utils.version_check.requests.get")
@patch("lottery_app.utils.version_check.__version__", "2.0.0")
def test_check_for_updates_no_update(
    mock_get,
    mock_auto_update,
    mock_app,
):
    mock_get.return_value.json.return_value = {
        "info": {"version": "2.0.0"}
    }

    check_for_updates(mock_app)

    mock_auto_update.assert_not_called()

# Exception during version check
@patch("lottery_app.utils.version_check.requests.get", side_effect=Exception("network down"))
def test_check_for_updates_exception_handled(
    mock_get,
    mock_app,
):
    check_for_updates(mock_app)

    mock_app.logger.warning.assert_called_once()
    
# Tests: auto_update
# Successful pip upgrade
@patch("lottery_app.utils.version_check.subprocess.run")
def test_auto_update_success(mock_run, mock_app):
    mock_run.return_value.stdout = b"updated"

    result = auto_update(mock_app, "lottery_app")

    assert result is True
    mock_run.assert_called_once()
    mock_app.logger.info.assert_called()

# pip upgrade fails
@patch("lottery_app.utils.version_check.flash")
@patch("lottery_app.utils.version_check.subprocess.run")
def test_auto_update_failure(mock_run, mock_flash, mock_app):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1,
        cmd="pip install",
    )

    result = auto_update(mock_app, "lottery_app")

    assert result is False

    # User-facing message
    mock_flash.assert_called_once_with(
        "Automatic update failed. Please update manually.",
        "error",
    )

    # Internal logging (don’t assert exact string — just that it happened)
    mock_app.logger.error.assert_called_once()
    logged_msg = mock_app.logger.error.call_args[0][0]
    assert "Auto-update failed" in logged_msg
    assert "pip install" in logged_msg
    assert "non-zero exit status" in logged_msg



# Tests: restart_app
# Flask process restart
@patch("lottery_app.utils.version_check.os.execv")
def test_restart_app_calls_execv(mock_execv, mock_app):
    restart_app(mock_app)

    python = sys.executable
    mock_execv.assert_called_once_with(
        python,
        [python] + sys.argv,
    )
    mock_app.logger.info.assert_called_once_with("Restarting Flask app...")