"""
Home route for the Lottery Management System.
Initializes the database and renders the home page.
"""


from flask import Blueprint, render_template

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET", "POST"])
def home():
    """
    Home route

    Returns:
        str: Rendered HTML for the home page.
    """
    
    return render_template("index.html")
