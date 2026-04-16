"""Tests for version_check utilities."""

import sys
from unittest.mock import MagicMock, patch

import pytest
import requests as req
from flask import Flask, get_flashed_messages

from lottery_app.utils.version_check import (
    check_for_updates,
    get_latest_github_version,
    is_bundled,
    notify_if_update_available,
    start_version_check,
)


@pytest.fixture
def app():
    """Minimal Flask app with a request context available for flash()."""
    flask_app = Flask(__name__)
    flask_app.secret_key = "test-secret"
    flask_app.config["TESTING"] = True
    return flask_app


# ---------------------------------------------------------------------------
# is_bundled
# ---------------------------------------------------------------------------


class TestIsBundled:
    def test_returns_false_in_normal_python(self):
        assert is_bundled() is False

    def test_returns_true_when_frozen_and_meipass_present(self):
        with patch.object(sys, "frozen", True, create=True), patch.object(
            sys, "_MEIPASS", "/tmp/meipass", create=True
        ):
            assert is_bundled() is True

    def test_returns_false_when_frozen_but_no_meipass(self):
        # Ensure _MEIPASS is absent even if frozen is set
        with patch.object(sys, "frozen", True, create=True):
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")
            assert is_bundled() is False


# ---------------------------------------------------------------------------
# get_latest_github_version
# ---------------------------------------------------------------------------


class TestGetLatestGithubVersion:
    def _mock_response(self, tag, url):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"tag_name": tag, "html_url": url}
        return resp

    def test_returns_cleaned_version_and_url(self):
        mock_resp = self._mock_response(
            "v1.2.3", "https://github.com/owner/repo/releases/tag/v1.2.3"
        )
        with patch("lottery_app.utils.version_check.requests.get", return_value=mock_resp):
            ver, url = get_latest_github_version()
        assert ver == "1.2.3"
        assert url == "https://github.com/owner/repo/releases/tag/v1.2.3"

    def test_strips_leading_v(self):
        mock_resp = self._mock_response("v2.0.0", "https://example.com")
        with patch("lottery_app.utils.version_check.requests.get", return_value=mock_resp):
            ver, _ = get_latest_github_version()
        assert ver == "2.0.0"

    def test_works_without_leading_v(self):
        mock_resp = self._mock_response("3.1.4", "https://example.com")
        with patch("lottery_app.utils.version_check.requests.get", return_value=mock_resp):
            ver, _ = get_latest_github_version()
        assert ver == "3.1.4"

    def test_raises_request_exception_on_network_error(self):
        with patch(
            "lottery_app.utils.version_check.requests.get",
            side_effect=req.RequestException("offline"),
        ):
            with pytest.raises(req.RequestException):
                get_latest_github_version()

    def test_raises_http_error_on_404(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req.HTTPError("404 Not Found")
        with patch("lottery_app.utils.version_check.requests.get", return_value=mock_resp):
            with pytest.raises(req.HTTPError):
                get_latest_github_version()


# ---------------------------------------------------------------------------
# check_for_updates
# ---------------------------------------------------------------------------


class TestCheckForUpdates:
    def test_flashes_warning_when_newer_version_available(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            return_value=("99.0.0", "https://github.com/releases"),
        ), patch("lottery_app.utils.version_check.is_bundled", return_value=False):
            with app.test_request_context("/"):
                check_for_updates(app)
                messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        category, msg = messages[0]
        assert category == "warning"
        assert "99.0.0" in msg

    def test_no_flash_when_already_up_to_date(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            return_value=("0.0.1", "https://github.com/releases"),
        ):
            with app.test_request_context("/"):
                check_for_updates(app)
                messages = get_flashed_messages(with_categories=True)
        assert messages == []

    def test_no_flash_on_network_error(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            side_effect=req.RequestException("no network"),
        ):
            with app.test_request_context("/"):
                check_for_updates(app)
                messages = get_flashed_messages(with_categories=True)
        assert messages == []

    def test_no_flash_on_404_no_releases(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            side_effect=req.HTTPError("404 Not Found"),
        ):
            with app.test_request_context("/"):
                check_for_updates(app)
                messages = get_flashed_messages(with_categories=True)
        assert messages == []

    def test_no_flash_on_malformed_api_response(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            side_effect=KeyError("tag_name"),
        ):
            with app.test_request_context("/"):
                check_for_updates(app)
                messages = get_flashed_messages(with_categories=True)
        assert messages == []

    def test_opens_browser_when_bundled_and_newer(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            return_value=("99.0.0", "https://github.com/releases"),
        ), patch(
            "lottery_app.utils.version_check.is_bundled", return_value=True
        ), patch(
            "lottery_app.utils.version_check.open_releases_page"
        ) as mock_open:
            with app.test_request_context("/"):
                check_for_updates(app)
            mock_open.assert_called_once()

    def test_does_not_open_browser_when_not_bundled(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            return_value=("99.0.0", "https://github.com/releases"),
        ), patch(
            "lottery_app.utils.version_check.is_bundled", return_value=False
        ), patch(
            "lottery_app.utils.version_check.open_releases_page"
        ) as mock_open:
            with app.test_request_context("/"):
                check_for_updates(app)
            mock_open.assert_not_called()

    def test_flash_message_contains_download_url_when_not_bundled(self, app):
        release_url = "https://github.com/owner/repo/releases/tag/v99.0.0"
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            return_value=("99.0.0", release_url),
        ), patch("lottery_app.utils.version_check.is_bundled", return_value=False):
            with app.test_request_context("/"):
                check_for_updates(app)
                messages = get_flashed_messages(with_categories=True)
        _, msg = messages[0]
        assert release_url in msg


# ---------------------------------------------------------------------------
# start_version_check
# ---------------------------------------------------------------------------


class TestStartVersionCheck:
    def test_stores_version_tuple_on_success(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            return_value=("99.0.0", "https://github.com/releases"),
        ):
            t = None
            original_thread = __import__("threading").Thread

            def capture_thread(*args, **kwargs):
                nonlocal t
                t = original_thread(*args, **kwargs)
                return t

            with patch("lottery_app.utils.version_check.threading.Thread", side_effect=capture_thread):
                start_version_check(app)
            t.join(timeout=2)

        assert app.config["_version_info"] == ("99.0.0", "https://github.com/releases")

    def test_stores_none_on_network_error(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            side_effect=req.RequestException("offline"),
        ):
            t = None
            original_thread = __import__("threading").Thread

            def capture_thread(*args, **kwargs):
                nonlocal t
                t = original_thread(*args, **kwargs)
                return t

            with patch("lottery_app.utils.version_check.threading.Thread", side_effect=capture_thread):
                start_version_check(app)
            t.join(timeout=2)

        assert app.config["_version_info"] is None

    def test_stores_none_on_malformed_response(self, app):
        with patch(
            "lottery_app.utils.version_check.get_latest_github_version",
            side_effect=KeyError("tag_name"),
        ):
            t = None
            original_thread = __import__("threading").Thread

            def capture_thread(*args, **kwargs):
                nonlocal t
                t = original_thread(*args, **kwargs)
                return t

            with patch("lottery_app.utils.version_check.threading.Thread", side_effect=capture_thread):
                start_version_check(app)
            t.join(timeout=2)

        assert app.config["_version_info"] is None


# ---------------------------------------------------------------------------
# notify_if_update_available
# ---------------------------------------------------------------------------


class TestNotifyIfUpdateAvailable:
    def test_does_nothing_while_check_still_running(self, app):
        # _version_info not yet set — check in flight
        with app.test_request_context("/"):
            notify_if_update_available(app)
            messages = get_flashed_messages(with_categories=True)
        assert messages == []
        assert "_version_notified" not in app.config

    def test_flashes_warning_when_newer_version_available(self, app):
        app.config["_version_info"] = ("99.0.0", "https://github.com/releases")
        with patch("lottery_app.utils.version_check.is_bundled", return_value=False):
            with app.test_request_context("/"):
                notify_if_update_available(app)
                messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 1
        category, msg = messages[0]
        assert category == "warning"
        assert "99.0.0" in msg

    def test_no_flash_when_already_up_to_date(self, app):
        app.config["_version_info"] = ("0.0.1", "https://github.com/releases")
        with app.test_request_context("/"):
            notify_if_update_available(app)
            messages = get_flashed_messages(with_categories=True)
        assert messages == []

    def test_no_flash_when_check_failed(self, app):
        app.config["_version_info"] = None
        with app.test_request_context("/"):
            notify_if_update_available(app)
            messages = get_flashed_messages(with_categories=True)
        assert messages == []

    def test_notifies_only_once_across_multiple_requests(self, app):
        app.config["_version_info"] = ("99.0.0", "https://github.com/releases")
        with patch("lottery_app.utils.version_check.is_bundled", return_value=False):
            with app.test_request_context("/"):
                notify_if_update_available(app)
            with app.test_request_context("/"):
                notify_if_update_available(app)
                messages = get_flashed_messages(with_categories=True)
        assert messages == []

    def test_opens_browser_when_bundled_and_newer(self, app):
        app.config["_version_info"] = ("99.0.0", "https://github.com/releases")
        with patch(
            "lottery_app.utils.version_check.is_bundled", return_value=True
        ), patch("lottery_app.utils.version_check.open_releases_page") as mock_open:
            with app.test_request_context("/"):
                notify_if_update_available(app)
        mock_open.assert_called_once()
