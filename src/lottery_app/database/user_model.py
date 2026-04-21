"""
User model for the lottery application.

Defines the User class used for authentication and user management,
backed by a SQLite database via Flask-Login.
"""

import logging
import sqlite3

from flask import flash
from flask_login import UserMixin

logger = logging.getLogger(__name__)
from werkzeug.security import generate_password_hash, check_password_hash

from lottery_app.decorators import get_db_cursor
from lottery_app.utils.config import db_path

DATABASE = db_path


class User(UserMixin):
    """Represents an authenticated user in the lottery application."""

    def __init__(self, user_id, username, password_hash, role="standard"):
        """
        Initialize a User instance.

        Args:
            user_id (int): The unique user ID from the database.
            username (str): The user's login name.
            password_hash (str): The hashed password string.
            role (str): The user's role. Defaults to 'standard'.
        """
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get_by_username(username):
        """
        Retrieve a User by their username.

        Args:
            username (str): The username to look up.

        Returns:
            User or None: A User instance if found, otherwise None.
        """
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return User(*row) if row else None

    @staticmethod
    def get_by_id(user_id):
        """
        Retrieve a User by their ID.

        Args:
            user_id (int): The user ID to look up.

        Returns:
            User or None: A User instance if found, otherwise None.
        """
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute("SELECT * FROM Users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return User(*row) if row else None

    @staticmethod
    def create(username, password, role="standard"):
        """
        Create a new user in the database.

        Args:
            username (str): The desired username (must be unique).
            password (str): The plaintext password to hash and store.
            role (str): The user's role. Defaults to 'standard'.
        """
        try:
            hashed = generate_password_hash(password)
            with get_db_cursor(DATABASE) as cursor:
                cursor.execute(
                    "INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, hashed, role),
                )
                flash("Account created! You can now log in.", "success")
        except sqlite3.IntegrityError:
            flash(
                "SQL IntegrityError occurred while creating the user. "
                "Try inputting a unique username.",
                "error",
            )
        except sqlite3.Error as e:
            logger.error("DB error creating user %r: %s", username, e)
            flash("An error occurred. Please try again.", "error")

    @staticmethod
    def delete(username):
        """
        Delete a user by username, unless they are a protected default_admin.

        Args:
            username (str): The username of the account to delete.
        """
        try:
            with get_db_cursor(DATABASE) as cursor:
                cursor.execute(
                    "SELECT role FROM Users WHERE username = ?", (username,)
                )
                result = cursor.fetchone()
                if result and result[0] == "default_admin":
                    flash("Cannot delete protected user.", "error")
                else:
                    cursor.execute(
                        "DELETE FROM Users WHERE username = ?", (username,)
                    )
                    flash(f"User '{username}' was deleted successfully.", "success")
        except sqlite3.IntegrityError as e:
            logger.error("DB integrity error deleting user %r: %s", username, e)
            flash("An error occurred. Please try again.", "error")
        except sqlite3.Error as e:
            logger.error("DB error deleting user %r: %s", username, e)
            flash("An error occurred. Please try again.", "error")

    @staticmethod
    def update_password(user_id, new_password):
        """
        Update the password hash for a given user.

        Args:
            user_id (int): The ID of the user whose password should be updated.
            new_password (str): The new plaintext password to hash and store.
        """
        hashed = generate_password_hash(new_password)
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute(
                "UPDATE Users SET password_hash = ? WHERE id = ?", (hashed, user_id)
            )

    def verify_password(self, password):
        """
        Check a plaintext password against the stored hash.

        Args:
            password (str): The plaintext password to verify.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return check_password_hash(self.password_hash, password)
