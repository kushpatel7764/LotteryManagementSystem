"""
Configuration utility module for managing database paths,
download locations, and application configuration settings.
"""

import json
import os
import queue
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import flash

instance_path = os.path.join(
    os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "instance_folder"
)
os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, "Lottery_Management_Database.db")
db_dir = instance_path

# Correct SQL path: point to the database folder
sql_file_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../database/Lottery_DB_Schema.sql")
)

__version__ = "0.1.0"

DEFAULT_DOWNLOADS_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"
)
BARCODE_QUEUE: queue.Queue = queue.Queue()


def load_config():
    """
    Loads the JSON configuration file.

    Returns:
        dict: The parsed configuration data.
    """
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def update_ticket_order(order):
    """
    Updates the ticket order in the configuration file.

    Args:
        order (string): New ticket order to be saved.
    """
    if not isinstance(order, str):
        raise TypeError("ticket_order must be a string")
    config = load_config()
    updated = config["ticket_order"] != order
    config["ticket_order"] = order
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    if updated:  # if ticket order was changed
        flash(f"Ticket Order Updated to {order} sucessfully.", "settings_success")


def update_invoice_output_path(invoice_output_path):
    """
    Updates the invoice output path in the configuration file.

    Args:
        invoice_output_path (str): Path where invoices should be saved.
    """
    if not isinstance(invoice_output_path, str):
        raise TypeError("invoice_output_path must be a string")
    config = load_config()
    updated = config["invoice_output_path"] != invoice_output_path
    config["invoice_output_path"] = invoice_output_path
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    if updated:
        flash(
            f"Output path updated to {instance_path} sucessfully.", "settings_success"
        )


def update_business_info(name, value):
    """
    Updates a specific business information field in the configuration file.

    Args:
        name (str): The configuration field to update.
        value (str): The new value for the field.
    """
    # Name of the business info you want to change in the config file
    # Value is the value it should be changed to
    if not isinstance(value, str):
        raise TypeError("value must be a string")
    updated = False
    config = load_config()

    updated = value not in (config[name], "")

    config[name] = value
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    if updated:
        flash(f"{name} is updated to {value} successfully.", "business-profile_success")


_DEFAULT_TIMEZONE = "America/New_York"


def get_timezone() -> str:
    """
    Return the configured IANA timezone string.

    Falls back to 'America/New_York' if the config key is missing or contains
    an unrecognised timezone name so the app never crashes on a bad value.
    """
    tz_str = load_config().get("timezone", _DEFAULT_TIMEZONE)
    try:
        ZoneInfo(tz_str)  # validate — raises ZoneInfoNotFoundError if invalid
        return tz_str
    except ZoneInfoNotFoundError:
        return _DEFAULT_TIMEZONE


def update_should_poll(set_val):
    """
    Persists the barcode-scanner polling toggle.

    Args:
        set_val (str): Any string — canonicalized to "true" or "false" before
            writing so the config file always contains a known value.
    """
    if not isinstance(set_val, str):
        raise TypeError("should_poll value must be a string")
    canonical = "true" if set_val.strip().lower() == "true" else "false"
    config = load_config()
    config["should_poll"] = canonical
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
