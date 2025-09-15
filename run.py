"""
Development entry point for the Flask-SocketIO app.
Runs with socketio.run() for hot reloads & debugging.
"""


# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order
import eventlet
eventlet.monkey_patch()
import sys
from pathlib import Path
# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.app import app, socketio

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
