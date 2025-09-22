"""
Main Flask application entry point.

This module initializes the Flask app, sets up Socket.IO for real-time events,
and registers all the blueprints for different routes.
"""

from flask import Flask, request, jsonify

from src.routes.books import books_bp
from src.routes.business_profile import business_profile_bp
from src.routes.home import home_bp
from src.routes.reports import report_bp
from src.routes.settings import settings_bp
from src.routes.tickets import tickets_bp

from src.utils.config import BARCODE_STACK
from threading import Lock
from src.utils.config import load_config

BARCODE_LOCK = Lock()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(home_bp)
app.register_blueprint(report_bp)
app.register_blueprint(tickets_bp)
app.register_blueprint(books_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(business_profile_bp)


#@socketio.on("connect")
def on_connect():
    """
    Handles a new client connection to the Socket.IO server.
    """
    print("Client connected")


@app.route("/receive", methods=["POST"])
def receive():
    """
    Receives a barcode via POST request and emits it to connected clients.

    Returns:
        str: A simple confirmation message.
    """
    config = load_config()
    if config.get("should_poll", False) == "false":
        print("Polling is disabled — barcode ignored")
        return "Ignored"
    barcode = request.form.get("barcode")
    print(f"Received barcode: {barcode}")
    #with app.app_context():
    BARCODE_STACK.append(barcode)
        #socketio.emit("barcode_scanned", {"barcode": barcode})
    return "Received"

@app.route("/check_barcode_stack", methods=["GET"])
def check():
    """
    Endpoint to check and retrieve the latest barcode from the queue.

    Returns:
        json: It contains the latest barcode or None if the queue is empty.
    """
    with BARCODE_LOCK:
        if BARCODE_STACK:
            barcode = BARCODE_STACK.pop()
            return jsonify({"barcode": barcode})
        return jsonify({"barcode": None})
