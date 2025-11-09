"""
Main Flask application entry point.

Pyinstaller Command: 
pyinstaller --onefile --noconsole  run.py 
"""

import sys # pylint: disable=wrong-import-position
from pathlib import Path # pylint: disable=wrong-import-order
# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from lottery_app import create_app
app = create_app()



def main():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()