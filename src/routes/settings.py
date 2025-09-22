"""
Settings routes for Lottery Management System.

This module provides:
- A route to manage system settings (ticket order and invoice output path).
- Helpers to extract form data and validate user-provided settings.
"""


import os

from flask import Blueprint, render_template, request

from src.utils.config import (DEFAULT_DOWNLOADS_PATH, load_config,
                          update_invoice_output_path, update_ticket_order,
                          update_should_poll)

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["GET", "POST"])
def settings():
    """
    Render and manage the settings page.

    Allows users to:
    - Update the ticket counting order.
    - Change the invoice output path (validated before saving).
    """
    message = None
    message_type = "warning"
    if request.method == "POST":
        config = load_config()

        # Process form input with fallback to config
        form_data = extract_setting_form_data(config)

        # Update ticket order
        update_ticket_order(form_data["ticket_order"])

        # Validate and update invoice output path
        valid_output, warning_message = validate_invoice_output_path(
            form_data["output_path"]
        )
        if warning_message:
            message = warning_message
        update_invoice_output_path(valid_output)
        
        update_should_poll(form_data["should_poll"])

    # Load current config for rendering
    config = load_config()
    return render_template(
        "settings.html",
        counting_order=config["ticket_order"],
        invoice_output_path=config["invoice_output_path"],
        should_poll=config["should_poll"],
        message=message,
        message_type=message_type,
    )


def extract_setting_form_data(config):
    """
    Extracts ticket order and invoice output path from the settings form.

    Args:
        config (dict): Existing configuration used as fallback.

    Returns:
        dict: Dictionary containing "ticket_order" and "output_path".
    """
    return {
        "ticket_order": request.form.get("ticket_order") or config["ticket_order"],
        "output_path": request.form.get("outputPath") or config["invoice_output_path"],
        "should_poll": request.form.get("polling_state") or config["should_poll"]
    }


def validate_invoice_output_path(path):
    """
    Validates the provided invoice output path.

    Args:
        path (str): Path provided by the user.

    Returns:
        tuple: (valid_path: str, warning_message: Optional[str])
    """
    if os.path.isdir(path):
        return path, None
    return DEFAULT_DOWNLOADS_PATH, "Resetting to DEFAULT PATH (invalid output path)"
