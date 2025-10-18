"""
Flask application initialization.

This module initializes the Flask app
and registers all the blueprints for different routes.
"""

from flask import Flask

from flask_login import LoginManager
from lottery_app.database.user_model import User
import os

from lottery_app.database import setup_database
from lottery_app.utils.config import db_path, sql_file_path
from lottery_app.routes.books import books_bp
from lottery_app.routes.business_profile import business_profile_bp
from lottery_app.routes.home import home_bp
from lottery_app.routes.reports import report_bp
from lottery_app.routes.settings import settings_bp
from lottery_app.routes.tickets import tickets_bp
from lottery_app.routes.scanner import scanner_bp
from lottery_app.routes.security import security_bp


def create_app():
    my_instance_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance_folder')
    app = Flask(__name__, instance_path=my_instance_location)
    app.secret_key = "your_secret_key"  # Replace with strong key

    # --- Initialize database inside app context ---
    with app.app_context():
        setup_database.initialize_database(db_path)
        print("Database initialized successfully!")

    # --- Setup login manager ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "security.login"
        
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    # Register blueprints
    app.register_blueprint(security_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(business_profile_bp)
    app.register_blueprint(scanner_bp)
    
    return app

