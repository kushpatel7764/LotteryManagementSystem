"""
Flask application initialization.

This module initializes the Flask app
and registers all the blueprints for different routes.
"""

from flask import Flask

from lottery_app.database import setup_database
from lottery_app.utils.config import db_path
from lottery_app.routes.books import books_bp
from lottery_app.routes.business_profile import business_profile_bp
from lottery_app.routes.home import home_bp
from lottery_app.routes.reports import report_bp
from lottery_app.routes.settings import settings_bp
from lottery_app.routes.tickets import tickets_bp
from lottery_app.routes.scanner import scanner_bp


def create_app():
    app = Flask(__name__)
    # initalize the database.
    setup_database.initialize_database(db_path)
    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(business_profile_bp)
    app.register_blueprint(scanner_bp)
    
    return app

