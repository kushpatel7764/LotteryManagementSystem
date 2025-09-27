"""
Flask application initialization.

This module initializes the Flask app
and registers all the blueprints for different routes.
"""

from flask import Flask

from src.routes.books import books_bp
from src.routes.business_profile import business_profile_bp
from src.routes.home import home_bp
from src.routes.reports import report_bp
from src.routes.settings import settings_bp
from src.routes.tickets import tickets_bp
from src.routes.scanner import scanner_bp


def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(business_profile_bp)
    app.register_blueprint(scanner_bp)
    
    return app

