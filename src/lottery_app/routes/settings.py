"""
Settings routes for Lottery Management System.
"""

from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, flash, redirect, url_for
from flask_login import login_required

from lottery_app.utils.config import (
    DEFAULT_DOWNLOADS_PATH,
    add_box_range,
    delete_box,
    get_boxes,
    load_config,
    update_invoice_output_path,
    update_ticket_order,
)
from lottery_app.utils.bluetooth_bridge import bluetooth_bridge

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        config = load_config()
        form_data = extract_setting_form_data(config)
        update_ticket_order(form_data["ticket_order"])
        valid_output, warning_message = validate_invoice_output_path(form_data["output_path"])
        if warning_message:
            flash(warning_message, "settings_warning")
        update_invoice_output_path(valid_output)

    config = load_config()
    return render_template(
        "settings.html",
        counting_order=config["ticket_order"],
        invoice_output_path=config["invoice_output_path"],
        bt_running=bluetooth_bridge.is_running,
        boxes=get_boxes(),
    )


@settings_bp.route("/settings/add_box_range", methods=["POST"])
@login_required
def add_box_range_route():
    add_box_range(
        request.form.get("box_range_start", ""),
        request.form.get("box_range_end", ""),
    )
    return redirect(url_for("settings.settings"))


@settings_bp.route("/settings/delete_box", methods=["POST"])
@login_required
def delete_box_route():
    delete_box(request.form.get("box_number", ""))
    return redirect(url_for("settings.settings"))


@settings_bp.route("/bluetooth", methods=["POST"])
@login_required
def toggle_bluetooth():
    action = request.form.get("action")
    if action == "start":
        bluetooth_bridge.start()
    elif action == "stop":
        bluetooth_bridge.stop()
    return redirect(url_for("settings.settings"))


@settings_bp.route("/bluetooth/status", methods=["GET"])
@login_required
def bluetooth_status():
    return jsonify({"status": bluetooth_bridge.status})


def extract_setting_form_data(config):
    return {
        "ticket_order": request.form.get("ticket_order") or config["ticket_order"],
        "output_path":  request.form.get("outputPath")   or config["invoice_output_path"],
    }


def validate_invoice_output_path(path):
    """
    Rejects any path that does not resolve to a directory inside the current
    user's home directory to block path-traversal attempts.
    """
    try:
        resolved = Path(path).resolve()
        home = Path.home()
        if resolved.is_dir() and resolved.is_relative_to(home):
            return str(resolved), None
    except (OSError, ValueError):
        pass
    return DEFAULT_DOWNLOADS_PATH, "Path must be a directory within your home folder."
