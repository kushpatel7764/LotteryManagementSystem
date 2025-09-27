"""
Home route for the Lottery Management System.
Initializes the database and renders the home page.
"""


from flask import Blueprint, render_template

from src.database import setup_database
from src.utils.config import db_path

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET", "POST"])
def home():
    """
    Home route that initializes the database and renders the index page.

    Returns:
        str: Rendered HTML for the home page.
    """
    # While loading the home page initalize the database.
    setup_database.initialize_database(db_path)
    return render_template("index.html")
