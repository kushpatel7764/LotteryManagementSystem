"""
Flask application initialization.

This module initializes the Flask app
and registers all the blueprints for different routes.
"""

import logging
import os
import atexit

logger = logging.getLogger(__name__)

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from lottery_app.database import setup_database
from lottery_app.database.user_model import User
from lottery_app.extensions import csrf, limiter
from lottery_app.utils.config import db_path
from lottery_app.routes.books import books_bp
from lottery_app.routes.business_profile import business_profile_bp
from lottery_app.routes.reports import report_bp
from lottery_app.routes.settings import settings_bp
from lottery_app.routes.tickets import tickets_bp
from lottery_app.routes.scanner import scanner_bp
from lottery_app.routes.security import security_bp
from lottery_app.utils.version_check import notify_if_update_available, start_version_check
from lottery_app.utils.encrypted_db import decrypt_file, encrypt_file


def encrypt_db_at_exit():
    """Encrypt the database file on application shutdown and 
    remove the plaintext copy."""
    enc_path = db_path + ".enc"
    if os.path.exists(db_path):
        encrypt_file(db_path, enc_path)
        os.remove(db_path)
        logger.debug("Database re-encrypted on app shutdown")


def create_app():
    """
    Create and configure the Flask application.
 
    Returns:
        Flask: The fully configured Flask application instance.
    """
    my_instance_location = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "instance_folder"
    )
    app = Flask(__name__, instance_path=my_instance_location)

    enc_path = db_path + ".enc"
    # Load .env file from project root
    load_dotenv()

    secret = os.getenv("FLASK_SECRET_KEY")
    if not secret:
        raise RuntimeError("FLASK_SECRET_KEY env var must be set")
    app.secret_key = secret

    # Check for FERMENT_KEY in environment, else generate and save it
    fernet_key = os.getenv("FERNET_KEY")

    if not fernet_key:
        raise RuntimeError(
            "FERNET_KEY is not set. Generate one with:\n"
            "  python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"\n"
            "then add FERNET_KEY=<value> to your .env file."
        )

    # Store it in Flask config
    app.config["FERNET_KEY"] = fernet_key
    app.fernet = Fernet(fernet_key.encode())

    # --- Decrypt database at startup ---
    if os.path.exists(enc_path):
        decrypt_file(enc_path, db_path)
        # Remove the encrypted copy now that plaintext is live.
        # Absence of .enc is the crash-detection sentinel: if .db is found
        # on the next startup without a matching .enc, the previous session
        # crashed before atexit could re-encrypt.
        os.remove(enc_path)
    elif os.path.exists(db_path):
        # .db present but no .enc means the previous session crashed after
        # decryption but before re-encryption.  The data is intact; a clean
        # exit will re-encrypt it.  Log the anomaly so operators can see it.
        logger.warning(
            "Plaintext database found with no encrypted backup. "
            "The previous session may have terminated uncleanly."
        )

    # --- Initialize database inside app context ---
    with app.app_context():
        setup_database.initialize_database(db_path)

    # --- Start background version check; notify on first eligible request ---
    # flash() requires a request context, so the network fetch runs in a daemon
    # thread (start_version_check) and the result is applied in before_request.
    start_version_check(app)

    @app.before_request
    def check_version_once():
        notify_if_update_available(app)

    # --- Initialize CSRF protection ---
    app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # token expires after 1 hour
    csrf.init_app(app)

    # --- Initialize rate limiter ---
    limiter.init_app(app)

    # --- Setup login manager ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "security.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    # Register blueprints
    app.register_blueprint(security_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(business_profile_bp)
    app.register_blueprint(scanner_bp)

    # Register the encrypt function to be called at exit
    atexit.register(encrypt_db_at_exit)

    return app
