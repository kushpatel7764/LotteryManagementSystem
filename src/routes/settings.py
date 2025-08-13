from flask import Blueprint, request, render_template
from utils.config import DEFAULT_DOWNLOADS_PATH, load_config, update_ticket_order, update_invoice_output_path
import os

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=["GET","POST"])
def settings():
    message = None
    message_type = "warning"
    if request.method == "POST":
        config = load_config()
    
        # Process form input with fallback to config
        form_data = extract_settingForm_data(config)

        # Update ticket order
        update_ticket_order(form_data["ticket_order"])

        # Validate and update invoice output path
        valid_output, warning_message = validate_invoice_output_path(form_data["output_path"])
        if warning_message:
            message = warning_message
        update_invoice_output_path(valid_output)

    # Load current config for rendering
    config = load_config()
    return render_template(
        "settings.html",
        counting_order=config["ticket_order"],
        invoice_output_path=config["invoice_output_path"],
        message=message,
        message_type=message_type
    )
    
def extract_settingForm_data(config):
    return {
        "ticket_order": request.form.get("ticket_order") or config["ticket_order"],
        "output_path": request.form.get("outputPath") or config["invoice_output_path"]
    }

def validate_invoice_output_path(path):
    if os.path.isdir(path):
        return path, None
    return DEFAULT_DOWNLOADS_PATH, "Resetting to DEFAULT PATH (invalid output path)"

