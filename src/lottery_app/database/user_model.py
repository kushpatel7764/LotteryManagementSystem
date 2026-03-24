from flask_login import UserMixin
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from lottery_app.decorators import get_db_cursor
from lottery_app.utils.config import db_path
from flask import flash

DATABASE = db_path  # 


class User(UserMixin):
    def __init__(self, id, username, password_hash, role="standard"):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get_by_username(username):
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return User(*row) if row else None

    @staticmethod
    def get_by_id(user_id):
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute("SELECT * FROM Users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return User(*row) if row else None

    @staticmethod
    def create(username, password, role="standard"):
        try:
            hashed = generate_password_hash(password)
            with get_db_cursor(DATABASE) as cursor:
                cursor.execute(
                    "INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, hashed, role),
                )
                flash("Account created! You can now log in.", "success")
        except sqlite3.IntegrityError:
             flash(f"SQL IntegrityError occured while creating the user. Try inputing an unique username.", "error") 
        except Exception as e:
            flash(f"Error creating user: {e}", "error")
        

    @staticmethod
    def delete(username):
        try:
            with get_db_cursor(DATABASE) as cursor:
                cursor.execute("""
                    SELECT role FROM Users Where id = ?
                """, (username,))
                
                result = cursor.fetchone()
                # if the user to be deleted is default_admin do not delete else delete. 
                if result and result[0] == "default_admin":
                    flash("Cannot delete protected user.", "error")
                else:
                    cursor.execute("DELETE FROM Users WHERE username = ?", (username,))
                    flash(f"User '{username}' was deleted successfully.", "success")
        except sqlite3.IntegrityError as e:
            flash(f"SQL IntegrityError occured while deleting user: {e}", "error") 
        except Exception as e:
            flash(f"Error deleting user: {e}", "error")

    @staticmethod
    def update_password(user_id, new_password):
        hashed = generate_password_hash(new_password)
        with get_db_cursor(DATABASE) as cursor:
            cursor.execute(
                "UPDATE Users SET password_hash = ? WHERE id = ?", (hashed, user_id)
            )

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
