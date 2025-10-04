"""
Configuration utility module for managing database paths, 
download locations, and application configuration settings.
"""


import json
import os
from importlib import resources

# Define project and database paths
#project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#db_dir = os.path.join(project_dir, "database")
#os.makedirs(db_dir, exist_ok=True)

#db_path = os.path.join(db_dir, "Lottery_Management_Database.db")
#sql_file_path = os.path.join(db_dir, "Lottery_DB_Schema.sql")

with resources.path("lottery_app.database", "Lottery_Management_Database.db") as db_file_path:
    db_path = str(db_file_path)
    db_dir = os.path.dirname(db_path)
    sql_file_path = os.path.join(db_dir, "Lottery_DB_Schema.sql")

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
    config = load_config()
    config["ticket_order"] = order
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def update_invoice_output_path(invoice_output_path):
    """
    Updates the invoice output path in the configuration file.

    Args:
        invoice_output_path (str): Path where invoices should be saved.
    """
    config = load_config()
    config["invoice_output_path"] = invoice_output_path
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def update_business_info(name, value):
    """
    Updates a specific business information field in the configuration file.

    Args:
        name (str): The configuration field to update.
        value (str): The new value for the field.
    """
    # Name of the business info you want to change in the config file
    # Value is the value it should be changed to
    config = load_config()
    config[name] = value
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

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
