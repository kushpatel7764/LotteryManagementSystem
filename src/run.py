"""
This module serves as the entry point for the application.
It initializes the Flask app and starts the server.
"""



import eventlet
eventlet.monkey_patch()

from src.app import app, socketio  # pylint: disable=wrong-import-position

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
