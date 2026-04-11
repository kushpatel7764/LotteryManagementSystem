"""
Main Flask application entry point.

Pyinstaller Command:
pyinstaller --onefile --noconsole  run.py
"""

import sys
import threading
import webbrowser
from pathlib import Path

def _ensure_project_on_path() -> None:
    """
    Insert the project root into sys.path if it is not already present.
 
    This must be called before any lottery_app imports are resolved so that
    Python can locate the package when the script is run directly (e.g.
    ``python app.py``) rather than as part of an installed distribution.
    """
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

_ensure_project_on_path()

from lottery_app import create_app  # pylint: disable=wrong-import-position

app = create_app()

PORT = 5000


def open_browser():
    """Open the default web browser at the login page."""
    webbrowser.open(f"http://127.0.0.1:{PORT}/login")

def run_server():
    """Start the Flask development server."""
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)

def launch_app():
    """Launch the Flask server and open the browser after a short delay."""
    threading.Thread(target=run_server).start()
    threading.Timer(1.5, open_browser).start()

if __name__ == "__main__":
    launch_app()
