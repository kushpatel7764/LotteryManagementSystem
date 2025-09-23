"""
Development entry point for the Flask-SocketIO app.
Runs with socketio.run() for hot reloads & debugging.

Pyinstaller Command: 
pyinstaller --onefile --noconsole --hidden-import=dns --hidden-import=dns.e164 
--hidden-import=dns.dnssec --hidden-import=dns.asyncbackend 
--hidden-import=dns.rdtypes.dnskeybase --hidden-import=dns.rdtypes.CH 
--hidden-import=dns.rdtypes --hidden-import=dns.rdtypes.ANY 
--hidden-import=dns.rdtypes.IN run.py --additional-hooks-dir=hooks

--------------------------------
Removing the socketio.
"""

# pylint: disable=wrong-import-position
# pylint: disable=wrong-import-order

import sys
from pathlib import Path
# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import webbrowser
from src.app import app

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
