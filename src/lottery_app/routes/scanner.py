"""
Scanner routes for the Flask application.
This module provides:
- A route to receive barcodes via POST requests.
- A route to check and retrieve the latest barcode from the stack.
"""

import logging
import os
import queue
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)
from flask_login import login_required

from lottery_app.extensions import csrf
from lottery_app.utils.config import BARCODE_QUEUE
from lottery_app.utils.config import load_config

_SCANNER_API_KEY = os.getenv("SCANNER_API_KEY")

scanner_bp = Blueprint("scanner", __name__)


@scanner_bp.route("/receive", methods=["POST"])
@csrf.exempt
def receive():
    """
    Receives a barcode via POST request and emits it to connected clients.

    Returns:
        str: A simple confirmation message.
    """
    if _SCANNER_API_KEY and request.headers.get("X-Scanner-Key") != _SCANNER_API_KEY:
        return "Unauthorized", 401

    config = load_config()
    should_poll = str(config.get("should_poll", "true")).lower() == "true"
    if not should_poll:
        return "Ignored"
    barcode = request.form.get("barcode")
    logger.debug("Received barcode: %s", barcode)
    BARCODE_QUEUE.put(barcode)
    return "Received"


@scanner_bp.route("/check_barcode_stack", methods=["GET"])
@login_required
def check():
    """
    Endpoint to check and retrieve the latest barcode from the queue.

    Returns:
        json: It contains the latest barcode or None if the queue is empty.
    """
    try:
        barcode = BARCODE_QUEUE.get_nowait()
        return jsonify({"barcode": barcode})
    except queue.Empty:
        return jsonify({"barcode": None})
