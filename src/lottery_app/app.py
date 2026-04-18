"""
Main Flask application entry point.

Pyinstaller Command:
pyinstaller lottery_app.spec
"""

import multiprocessing
import os
import sys
import threading
import webbrowser
from pathlib import Path


PORT = 7777


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


def open_browser():
    """Open the default web browser at the login page."""
    webbrowser.open(f"http://127.0.0.1:{PORT}/login")


def launch_app(flask_app):
    """Launch the Flask server and open the browser after a short delay."""
    threading.Timer(1.5, open_browser).start()

    # Debug mode must be explicitly opted into via environment variable.
    # Never rely on the frozen-bundle check — that would silently enable the
    # Werkzeug interactive debugger (a Python shell in the browser) whenever
    # the app is run from source, including on misconfigured machines where
    # the port is reachable from other hosts.
    debug = os.getenv("FLASK_DEBUG", "0") == "1"

    flask_app.run(host="0.0.0.0", port=PORT, debug=debug, use_reloader=False)


if __name__ == "__main__":
    # freeze_support() MUST be the very first call inside __main__ for
    # PyInstaller + macOS (spawn mode).  Without it, any multiprocessing
    # worker process re-runs this entire script — including create_app() and
    # app.run() — which immediately hits a "port already in use" error and
    # loops forever.
    multiprocessing.freeze_support()

    # Path fixup and app creation stay inside __main__ so they are skipped
    # entirely when the frozen binary is re-invoked as a multiprocessing
    # worker (freeze_support() returns early in that case).
    _ensure_project_on_path()

    from lottery_app import create_app  # pylint: disable=wrong-import-position

    app = create_app()
    launch_app(app)
