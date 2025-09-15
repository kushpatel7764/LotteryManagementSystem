"""
WSGI entry point for production with Gunicorn + SocketIO.
"""

from src.app import app

# Gunicorn will look for "app" here
# If needed, you can also serve via socketio, e.g., socketio.WSGIApp(app)
application = app
