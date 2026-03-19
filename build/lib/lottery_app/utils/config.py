"""
Configuration utility module for managing database paths,
download locations, and application configuration settings.
"""

import json
import os
from flask import flash

# Define project and database paths
# project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# db_dir = os.path.join(project_dir, "database")
# os.makedirs(db_dir, exist_ok=True)

# db_path = os.path.join(db_dir, "Lottery_Management_Database.db")
# sql_file_path = os.path.join(db_dir, "Lottery_DB_Schema.sql")

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
BARCODE_STACK = []


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
        order (list): New ticket order to be saved.
    """
    updated = False
    config = load_config()
    if config["ticket_order"] != order:
        updated = True
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
    updated = False
    config = load_config()
    if config["invoice_output_path"] != invoice_output_path:
        updated = True
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
    updated = False
    config = load_config()

    if config[name] != value and value != "":
        updated = True

    config[name] = value
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    if updated:
        flash(f"{name} is updated to {value} successfully.", "business-profile_success")


def update_should_poll(set_val):
    """
    Updates a specific business information field in the configuration file.

    Args:
        name (str): The configuration field to update.
        value (str): The new value for the field.
    """
    # Name of the business info you want to change in the config file
    # Value is the value it should be changed to
    config = load_config()
    config["should_poll"] = set_val
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
