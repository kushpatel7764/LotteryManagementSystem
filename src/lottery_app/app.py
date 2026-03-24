"""
Main Flask application entry point.

Pyinstaller Command:
pyinstaller --onefile --noconsole  run.py
"""

import sys  # pylint: disable=wrong-import-position
from pathlib import Path  # pylint: disable=wrong-import-order
import webbrowser
import threading

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from lottery_app import create_app

app = create_app()

PORT = 5000 

# On app click open browser at login page
def open_browser():
    webbrowser.open(f"http://127.0.0.1:{PORT}/login")

# On app click run the flask server
def run_server():
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
    
def launch_app():
    threading.Thread(target=run_server).start()
    threading.Timer(1.5, open_browser).start()

if __name__ == "__main__":
    launch_app()
