from flask import Blueprint, render_template
from database import Database
from utils.config import db_path

home_bp = Blueprint("home", __name__)


@home_bp.route("/", methods=["GET", "POST"])
def home():
    # While loading the home page initalize the database.
    Database.initialize_database(db_path)
    return render_template("index.html")
