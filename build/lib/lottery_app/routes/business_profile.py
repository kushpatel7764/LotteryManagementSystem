"""
Business Profile Route

This module provides the Flask route and helper functions for managing
the business profile information (name, address, phone, email).
"""


import re
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from werkzeug.security import generate_password_hash
from lottery_app.utils.config import load_config, update_business_info, db_path
from lottery_app.database.database_queries import get_all_users

business_profile_bp = Blueprint("business_profile", __name__)


@business_profile_bp.route("/business_profile", methods=["GET", "POST"])
@login_required
def business_profile():
    """
    Handle the business profile page.

    - On GET: Renders the business profile with current configuration values.
    - On POST: Processes submitted form data, validates it, and updates the configuration.
    """
    message = None
    message_type = "error"
    if request.method == "POST":
        config = load_config()

        # Process form input with fallback to config
        form_data = extract_business_profile_form_data(config)

        # Validate and update business info fields
        errors = validate_and_update_business_info(form_data)
        if errors:
            message = errors[0]  # Only show the first error
        else:
            message = "Business profile updated successfully."
            message_type = "success"

    # Load current config for rendering
    config = load_config()
    users = get_all_users(db_path)
    return render_template(
        "business_profile.html",
        business_Info={
            "Name": config["business_name"],
            "Address": config["business_address"],
            "Phone": config["business_phone"],
            "Email": config["business_email"],
        },
        users=users,
        message=message,
        message_type=message_type,
    )


def extract_business_profile_form_data(config):
    """
    Extracts business profile form data, falling back to existing config values.

    Args:
        config (dict): The current business configuration.

    Returns:
        dict: A dictionary containing the form data for name, address, phone, and email.
    """
    return {
        "business_name": request.form.get("BusinessName") or config["business_name"],
        "business_address": request.form.get("BusinessAddress")
        or config["business_address"],
        "business_phone": request.form.get("BusinessPhone") or config["business_phone"],
        "business_email": request.form.get("BusinessEmail") or config["business_email"],
    }


def validate_and_update_business_info(data):
    """
    Validates and updates business profile information.

    Args:
        data (dict): The business profile fields to validate.

    Returns:
        list: A list of error messages, empty if all fields are valid.
    """
    errors = []

    # Business Name (always updated without validation)
    update_business_info(name="business_name", value=data["business_name"])

    # Address validation
    address = data["business_address"]
    if address == "" or re.match(
        "^(\\d{1,}) [a-zA-Z0-9\\s]+(\\,)? [a-zA-Z]+(\\,)? [A-Z]{2} [0-9]{5,6}$",
            address):
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
    if email == "" or re.fullmatch(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email
    ):
        update_business_info(name="business_email", value=email)
    else:
        update_business_info(name="business_email", value="")
        errors.append("Not a valid EMAIL!")

    return errors

def get_db_conn():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

