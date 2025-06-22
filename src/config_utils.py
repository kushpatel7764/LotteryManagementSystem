import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def update_ticket_order(order):
    config = load_config()
    config['ticket_order'] = order
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
