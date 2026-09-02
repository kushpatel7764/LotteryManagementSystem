"""
Main Flask application entry point.

Pyinstaller Command:
pyinstaller lottery_app.spec
"""

import datetime
import multiprocessing
import os
import sys
import threading
import traceback
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


def _setup_crash_logging() -> None:
    """
    Redirect stdout/stderr and any uncaught exception to a log file.

    Only takes effect in a PyInstaller-frozen build (``sys.frozen``). The
    packaged app is built with ``console=False``, so there is no terminal to
    show output or a crash traceback on — without this, both would simply be
    lost. Running from source (``python app.py``) is unaffected; output still
    goes to the terminal as normal.
    """
    if not getattr(sys, "frozen", False):
        return

    from lottery_app.utils.config import instance_path  # pylint: disable=import-outside-toplevel

    log_path = os.path.join(instance_path, "error_log.txt")
    log_file = open(  # pylint: disable=consider-using-with
        log_path, "a", encoding="utf-8", buffering=1
    )

    sys.stdout = log_file
    sys.stderr = log_file

    def log_uncaught_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"\n[{timestamp}] Uncaught exception:\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=log_file)
        log_file.flush()

    sys.excepthook = log_uncaught_exception


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
    _setup_crash_logging()

    from lottery_app import create_app  # pylint: disable=wrong-import-position

    app = create_app()
    launch_app(app)
