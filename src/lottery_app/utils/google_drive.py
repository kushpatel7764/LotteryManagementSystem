"""
Google Drive backup integration.

Lets the store owner back up the plaintext SQLite database to their own
Google Drive, either automatically after each daily submit or manually from
Settings. Uses a standard OAuth 2.0 "Desktop app" flow: the store owner signs
in once from Settings, and the resulting refresh token is kept locally so
later backups don't need any further interaction.
"""

import logging
import os
import threading
from datetime import datetime

from lottery_app.utils.config import db_path, instance_path

logger = logging.getLogger(__name__)

# credentials.json is the OAuth client secret downloaded from Google Cloud
# Console (APIs & Services > Credentials > Desktop app). It identifies this
# app to Google, not any particular user, so it ships alongside config.json.
CREDENTIALS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "credentials.json"
)
# The signed-in user's token. Grants access to only what this app created in
# their Drive (drive.file scope) plus their email address for display.
TOKEN_PATH = os.path.join(instance_path, "google_drive_token.json")

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

BACKUP_FOLDER_NAME = "Lottery Management Backups"

_state_lock = threading.Lock()
_connect_state = {"status": "idle", "message": ""}  # idle | connecting | connected | error


def has_credentials_file():
    """Whether the OAuth client secret (credentials.json) has been provided."""
    return os.path.exists(CREDENTIALS_PATH)


def is_connected():
    """Whether a Google account is currently linked."""
    return os.path.exists(TOKEN_PATH)


def disconnect():
    """Removes the stored token, unlinking the Google account."""
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)
    with _state_lock:
        _connect_state["status"] = "idle"
        _connect_state["message"] = ""


def get_connect_status():
    """Returns the current state of an in-progress or finished connect attempt."""
    with _state_lock:
        return dict(_connect_state)


def start_connect_flow():
    """
    Starts the OAuth consent flow in a background thread.

    The flow opens the user's browser to Google's consent page and blocks
    until they finish (or cancel), so it must not run on the Flask request
    thread. The Settings page polls get_connect_status() to find out when
    it's done.
    """
    with _state_lock:
        if _connect_state["status"] == "connecting":
            return
        _connect_state["status"] = "connecting"
        _connect_state["message"] = ""

    threading.Thread(target=_run_connect_flow, daemon=True).start()


def _run_connect_flow():
    try:
        if not has_credentials_file():
            raise FileNotFoundError(
                "credentials.json not found. Download an OAuth Desktop app "
                "client from Google Cloud Console and place it at "
                f"{CREDENTIALS_PATH}."
            )

        # Imported lazily so the rest of the app works even if these
        # (optional, Drive-only) packages aren't installed.
        from google_auth_oauthlib.flow import InstalledAppFlow  # pylint: disable=import-outside-toplevel

        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        _save_credentials(creds)

        with _state_lock:
            _connect_state["status"] = "connected"
            _connect_state["message"] = ""
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Google Drive connection failed: %s", e)
        with _state_lock:
            _connect_state["status"] = "error"
            _connect_state["message"] = str(e)


def _save_credentials(creds):
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def _load_credentials():
    if not os.path.exists(TOKEN_PATH):
        return None

    from google.auth.transport.requests import Request  # pylint: disable=import-outside-toplevel
    from google.oauth2.credentials import Credentials  # pylint: disable=import-outside-toplevel

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_credentials(creds)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to refresh Google Drive token: %s", e)
            return None
    return creds


def get_connected_email():
    """Returns the linked Google account's email, or None if unavailable."""
    creds = _load_credentials()
    if not creds:
        return None
    try:
        from googleapiclient.discovery import build  # pylint: disable=import-outside-toplevel

        service = build("oauth2", "v2", credentials=creds, cache_discovery=False)
        return service.userinfo().get().execute().get("email")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to fetch connected Google account email: %s", e)
        return None


def _get_or_create_backup_folder(service):
    query = (
        f"name = '{BACKUP_FOLDER_NAME}' and "
        "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)")
        .execute()
    )
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    folder = (
        service.files()
        .create(
            body={
                "name": BACKUP_FOLDER_NAME,
                "mimeType": "application/vnd.google-apps.folder",
            },
            fields="id",
        )
        .execute()
    )
    return folder["id"]


def backup_database(label=None):
    """
    Uploads the current SQLite database file to the user's Google Drive.

    Args:
        label (str, optional): Included in the uploaded filename (e.g. a
            report ID) so automatic post-submit backups are distinguishable
            from manual ones.

    Returns:
        tuple: (message, message_type)
    """
    creds = _load_credentials()
    if not creds:
        return "GOOGLE DRIVE IS NOT CONNECTED.", "error"

    try:
        from googleapiclient.discovery import build  # pylint: disable=import-outside-toplevel
        from googleapiclient.http import MediaFileUpload  # pylint: disable=import-outside-toplevel

        service = build("drive", "v3", credentials=creds, cache_discovery=False)
        folder_id = _get_or_create_backup_folder(service)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        suffix = f"_{label}" if label else ""
        filename = f"Lottery_Management_Database{suffix}_{timestamp}.db"

        media = MediaFileUpload(db_path, mimetype="application/x-sqlite3", resumable=False)
        service.files().create(
            body={"name": filename, "parents": [folder_id]},
            media_body=media,
            fields="id",
        ).execute()

        return f"DATABASE BACKED UP TO GOOGLE DRIVE AS {filename}", "success"
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning("Google Drive backup failed: %s", e)
        return f"GOOGLE DRIVE BACKUP FAILED: {e}", "error"
