"""
Settings routes for Lottery Management System.

This module provides:
- A route to manage system settings (ticket order and invoice output path).
- Helpers to extract form data and validate user-provided settings.
"""

from pathlib import Path

from flask import Blueprint, render_template, request, flash
from flask_login import login_required

from lottery_app.utils.config import (
    DEFAULT_DOWNLOADS_PATH,
    load_config,
    update_invoice_output_path,
    update_ticket_order,
    update_should_poll,
)

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """
    Render and manage the settings page.

    Allows users to:
    - Update the ticket counting order.
    - Change the invoice output path (validated before saving).
    """
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
            flash(warning_message, "settings_warning")
        update_invoice_output_path(valid_output)
        update_should_poll(form_data["should_poll"])

    # Load current config for rendering
    config = load_config()
    return render_template(
        "settings.html",
        counting_order=config["ticket_order"],
        invoice_output_path=config["invoice_output_path"],
        should_poll=config["should_poll"],
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
        "should_poll": (
            "true"
            if request.form.get("polling_state", "").strip().lower() == "true"
            else "false"
        ),
    }


def validate_invoice_output_path(path):
    """
    Validates the provided invoice output path.

    Rejects any path that does not resolve to a directory inside the current
    user's home directory.  This prevents invoices from being written to
    system directories (/etc, /tmp, network shares, etc.) and blocks
    path-traversal attempts before they reach the filesystem.

    Args:
        path (str): Path provided by the user.

    Returns:
        tuple: (valid_path: str, warning_message: Optional[str])
    """
    try:
        resolved = Path(path).resolve()
        home = Path.home()
        if resolved.is_dir() and resolved.is_relative_to(home):
            return str(resolved), None
    except (OSError, ValueError):
        pass

    return DEFAULT_DOWNLOADS_PATH, "Path must be a directory within your home folder."
