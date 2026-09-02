"""
Configuration utility module for managing database paths,
download locations, and application configuration settings.
"""

import json
import os
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

__version__ = "0.2.3"

DEFAULT_DOWNLOADS_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"
)

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


def get_boxes():
    """
    Returns the configured list of box numbers/labels.

    Falls back to an empty list if the config file predates this setting.
    """
    return load_config().get("boxes", [])


MAX_BOX_RANGE_SIZE = 500


def add_box_range(start, end):
    """
    Adds a numbered range of boxes (inclusive) to the configured list of boxes,
    e.g. start=1, end=20 adds boxes "1" through "20".

    Args:
        start (int): First box number in the range.
        end (int): Last box number in the range.
    """
    try:
        start = int(start)
        end = int(end)
    except (TypeError, ValueError):
        flash("Box range must be numbers.", "settings_warning")
        return

    if start < 1 or end < start:
        flash("Box range must count up from 1 or higher.", "settings_warning")
        return

    if end - start + 1 > MAX_BOX_RANGE_SIZE:
        flash(f"Box range can't be more than {MAX_BOX_RANGE_SIZE} boxes at once.", "settings_warning")
        return

    config = load_config()
    boxes = config.get("boxes", [])
    added = 0
    for number in range(start, end + 1):
        label = str(number)
        if label not in boxes:
            boxes.append(label)
            added += 1

    if added:
        config["boxes"] = boxes
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        flash(f"Added {added} box{'es' if added != 1 else ''}.", "settings_success")
    else:
        flash("Those boxes already exist.", "settings_warning")


def delete_box(box_number):
    """
    Removes a box number/label from the configured list of boxes.

    Args:
        box_number (str): The box number/label to remove.
    """
    config = load_config()
    boxes = config.get("boxes", [])
    if box_number in boxes:
        boxes.remove(box_number)
        config["boxes"] = boxes
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        flash(f"Box {box_number} removed.", "settings_success")


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


