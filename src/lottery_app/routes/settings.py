"""
Settings routes for Lottery Management System.
"""

from pathlib import Path

from flask import Blueprint, current_app, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required

from lottery_app.utils.auto_updater import apply_update, get_state, start_download
from lottery_app.utils.config import (
    DEFAULT_DOWNLOADS_PATH,
    load_config,
    update_invoice_output_path,
    update_ticket_order,
)
from lottery_app.utils.bluetooth_bridge import bluetooth_bridge
from lottery_app.utils.version_check import is_bundled

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
    update_available = current_app.config.get("_update_available", False) and is_bundled()
    return render_template(
        "settings.html",
        counting_order=config["ticket_order"],
        invoice_output_path=config["invoice_output_path"],
        bt_running=bluetooth_bridge.is_running,
        update_available=update_available,
        update_version=current_app.config.get("_update_version", ""),
    )


@settings_bp.route("/update/start", methods=["POST"])
@login_required
def update_start():
    if not is_bundled():
        return jsonify({"error": "Auto-update only works in the installed app."}), 400
    start_download()
    return jsonify({"status": "started"})


@settings_bp.route("/update/status")
@login_required
def update_status():
    return jsonify(get_state())


@settings_bp.route("/update/apply", methods=["POST"])
@login_required
def update_apply():
    try:
        apply_update()
        return jsonify({"status": "applying"})
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400


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
