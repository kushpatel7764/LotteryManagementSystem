"""
Scanner routes for the Flask application.
This module provides:
- A route to receive barcodes via POST requests.
- A route to check and retrieve the latest barcode from the stack.
"""
from threading import Lock
from flask import Blueprint, request, jsonify
from flask_login import login_required

from lottery_app.utils.config import BARCODE_STACK

from lottery_app.utils.config import load_config

BARCODE_LOCK = Lock()

scanner_bp = Blueprint("scanner", __name__)

@scanner_bp.route("/receive", methods=["POST"])
@login_required
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

@scanner_bp.route("/check_barcode_stack", methods=["GET"])
@login_required
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
