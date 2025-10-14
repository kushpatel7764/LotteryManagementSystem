"""
Home route for the Lottery Management System.
Initializes the database and renders the home page.
"""


from flask import Blueprint, render_template
from flask_login import login_required

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    """
    Home route

    Returns:
        str: Rendered HTML for the home page.
    """
    
    return render_template("index.html")
