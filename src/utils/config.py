import json
import os


project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_dir, 'Lottery_Management_Database.db')    

DEFAULT_DOWNLOADS_PATH = os.path.join(os.path.expanduser("~"), "Downloads")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def update_ticket_order(order):
    config = load_config()
    config['ticket_order'] = order
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

def update_invoice_output_path(invoice_output_path):
    config = load_config()
    config['invoice_output_path'] = invoice_output_path
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
def update_business_info(name, value):
    #Name of the business info you want to change in the config file
    #Value is the value it should be changed to
    config = load_config()
    config[name] = value
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)