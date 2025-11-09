import requests
import subprocess
import sys
import os
from packaging import version
from flask import flash
from lottery_app.utils.config import __version__

def check_for_updates(app, package_name="lottery_app"):
    """
    Check PyPI for a new version. If found, update the package and restart Flask.
    """
    try:
        # TestPyPI JSON API for package info : https://test.pypi.org/pypi/{package_name}/json
        # PyPI JSON API for package info : https://pypi.org/pypi/{package_name}/json
        resp = requests.get(f"https://test.pypi.org/pypi/{package_name}/json", timeout=5)
        latest_version = resp.json()["info"]["version"]
        print(f"__version__ = {version.parse(__version__)}")
        print(f" latest_version = {version.parse(latest_version)}")
        if version.parse(latest_version) > version.parse(__version__):
            flash(
                f"New version {latest_version} available! "
                f"Updating from {__version__} ...",
                "warning",
            )
            app.logger.info(f"Updating {package_name} from {__version__} to {latest_version}")
            success = auto_update(app, package_name)

            if success:
                flash("Update complete! Restarting app...", "success")
                restart_app(app)
    except Exception as e:
        app.logger.warning(f"Version check failed: {e}")

def auto_update(app, package_name):
    """Perform pip install --upgrade on the given package."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        app.logger.info(result.stdout.decode())
        return True
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Auto-update failed: {e}")
        flash("Automatic update failed. Please update manually.", "error")
        return False

def restart_app(app):
    """Restart the Flask process with the new version."""
    app.logger.info("Restarting Flask app...")
    python = sys.executable
    os.execv(python, [python] + sys.argv)
