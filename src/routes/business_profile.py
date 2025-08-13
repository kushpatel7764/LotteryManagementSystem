from flask import Blueprint, request, render_template
from utils.config import load_config, update_business_info
import re

business_profile_bp = Blueprint('business_profile', __name__)

@business_profile_bp.route('/business_profile', methods=["GET","POST"])
def business_profile():
    message = None
    message_type = "error"
    if request.method == "POST":
        config = load_config()
        
        # Process form input with fallback to config
        form_data = extract_businessProfileForm_data(config)
        
        # Validate and update business info fields
        errors = validate_and_update_business_info(form_data)
        if errors:
            message = errors[0]  # Only show the first error
        else:
            message = "Business profile updated successfully."
            message_type = "success"
    
    # Load current config for rendering
    config = load_config()
    return render_template(
        "business_profile.html",
        business_Info={
            "Name": config["business_name"],
            "Address": config["business_address"],
            "Phone": config["business_phone"],
            "Email": config["business_email"],
        },
        message=message,
        message_type=message_type
    )

def extract_businessProfileForm_data(config):
    return {
        "business_name": request.form.get("BusinessName") or config["business_name"],
        "business_address": request.form.get("BusinessAddress") or config["business_address"],
        "business_phone": request.form.get("BusinessPhone") or config["business_phone"],
        "business_email": request.form.get("BusinessEmail") or config["business_email"]
    }

def validate_and_update_business_info(data):
    errors = []

    # Business Name (always updated without validation)
    update_business_info(name="business_name", value=data["business_name"])

    # Address validation
    address = data["business_address"]
    if address == "" or re.match("^(\\d{1,}) [a-zA-Z0-9\\s]+(\\,)? [a-zA-Z]+(\\,)? [A-Z]{2} [0-9]{5,6}$", address):
        update_business_info(name="business_address", value=address)
    else:
        update_business_info(name="business_address", value="")
        errors.append("Not a valid ADDRESS!")

    # Phone number validation
    phone = data["business_phone"]
    if phone == "" or re.fullmatch(r"^\+?\d{10,15}$", phone):
        update_business_info(name="business_phone", value=phone)
    else:
        update_business_info(name="business_phone", value="")
        errors.append("Not a valid PHONE NUMBER!")

    # Email validation (allow empty field)
    email = data["business_email"]
    if email == "" or re.fullmatch(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        update_business_info(name="business_email", value=email)
    else:
        update_business_info(name="business_email", value="")
        errors.append("Not a valid EMAIL!")

    return errors