"""User model for the lottery application."""
from flask import flash
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from lottery_app.decorators import get_db_cursor
from lottery_app.utils.config import db_path

DATABASE = db_path  # Update with your actual db path


class User(UserMixin):
    """Represents an authenticated application user."""

    def __init__(self, user_id, username, password_hash, role="standard"):
        self.id = user_id  # pylint: disable=invalid-name
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get_by_username(username):
        """Return the User with the given username, or None."""
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return User(*row) if row else None

    @staticmethod
    def get_by_id(user_id):
        """Return the User with the given id, or None."""
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute("SELECT * FROM Users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return User(*row) if row else None

    @staticmethod
    def create(username, password, role="standard"):
        """Insert a new user with a hashed password."""
        hashed = generate_password_hash(password)
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute(
                "INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, hashed, role),
            )

    @staticmethod
    def delete(username):
        """Delete the user with the given username."""
        try:
            with get_db_cursor(DATABASE) as cursor:
                cursor.execute("DELETE FROM Users WHERE username = ?", (username,))
                flash(f"User '{username}' was deleted successfully.", "success")
        except Exception as e:  # pylint: disable=broad-exception-caught
            flash(f"Error deleting user: {e}", "error")

    @staticmethod
    def update_password(user_id, new_password):
        """Update the password hash for the given user id."""
        hashed = generate_password_hash(new_password)
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute(
                "UPDATE Users SET password_hash = ? WHERE id = ?", (hashed, user_id)
            )

    def verify_password(self, password):
        """Return True if the given password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
