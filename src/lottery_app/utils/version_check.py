"""
Version checking utilities for the lottery application.

Compares the currently installed version against the latest release published
on GitHub. Designed to work correctly when the application is bundled as a
PyInstaller executable, where pip-based auto-updating is not possible.

Instead of attempting an in-process upgrade, this module notifies the user
that a new version is available and opens the GitHub releases page so they
can download and replace the executable manually.
"""

import sys
import webbrowser

import requests
from flask import flash
from packaging import version

from lottery_app.utils.config import __version__

# Replace with your actual GitHub username and repository name
GITHUB_USER = "your-github-username"
GITHUB_REPO = "your-repo-name"

GITHUB_API_URL = (
    f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
)
GITHUB_RELEASES_URL = (
    f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
)


def is_bundled():
    """
    Detect whether the application is running as a PyInstaller executable.

    Returns:
        bool: ``True`` if running inside a PyInstaller bundle, ``False``
            if running as a normal Python script.
    """
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_latest_github_version():
    """
    Fetch the latest release tag from the GitHub Releases API.

    Strips a leading ``v`` from the tag name so that tags like ``v1.2.3``
    can be compared directly against PEP 440 version strings.

    Returns:
        tuple[str, str]: A ``(version_string, release_url)`` pair where
            ``version_string`` is the cleaned version number and
            ``release_url`` is the HTML URL of the release page.

    Raises:
        requests.RequestException: If the HTTP request fails or times out.
        KeyError: If the API response does not contain the expected fields.
    """
    resp = requests.get(
        GITHUB_API_URL,
        timeout=5,
        headers={"Accept": "application/vnd.github+json"},
    )
    resp.raise_for_status()
    data = resp.json()
    tag = data["tag_name"].lstrip("v")
    url = data["html_url"]
    return tag, url


def open_releases_page():
    """Open the GitHub releases page in the user's default web browser."""
    webbrowser.open(GITHUB_RELEASES_URL)


def check_for_updates(app):
    """
    Compare the running version against the latest GitHub release.

    Behaviour differs depending on how the application is launched:

    - **PyInstaller executable** — auto-updating via pip is not possible.
      If a newer release is found, the user is notified via a flash message
      and the GitHub releases page is opened in their browser so they can
      download and replace the executable manually.

    - **Plain Python** — the user is notified via flash and a log message.
      No automatic installation is attempted; the update instructions point
      to GitHub so the workflow stays consistent with the bundled case.

    Args:
        app (Flask): The active Flask application instance, used for logging
            and flashing in-app messages.
    """
    try:
        latest, release_url = get_latest_github_version()

        if version.parse(latest) > version.parse(__version__):
            app.logger.info(
                "New version available: %s (running %s). Release: %s",
                latest,
                __version__,
                release_url,
            )

            if is_bundled():
                # Running as a .exe — direct the user to download the new build
                flash(
                    f"A new version ({latest}) is available! "
                    "Opening the download page in your browser...",
                    "warning",
                )
                open_releases_page()
            else:
                # Running as a plain Python script
                flash(
                    f"A new version ({latest}) is available. "
                    f"Download it from: {release_url}",
                    "warning",
                )
        else:
            app.logger.info("Application is up to date (version %s).", __version__)

    except requests.RequestException as e:
        # Network / HTTP errors are expected in offline environments
        app.logger.warning("Version check failed (network): %s", e)
    except (KeyError, ValueError) as e:
        # Malformed GitHub API response
        app.logger.warning("Version check failed (parse error): %s", e)
