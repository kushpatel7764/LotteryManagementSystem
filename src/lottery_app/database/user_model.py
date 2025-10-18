from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from lottery_app.utils.config import db_path
import sqlite3

DATABASE = db_path # Update with your actual db path

class User(UserMixin):
    def __init__(self, id, username, password_hash, role='standard'):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return User(*row) if row else None

    @staticmethod
    def get_by_id(user_id):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return User(*row) if row else None

    @staticmethod
    def create(username, password, role='standard'):
        hashed = generate_password_hash(password)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, hashed, role)
        )
        conn.commit()
        conn.close()
        
    @staticmethod
    def update_password(user_id, new_password):
        hashed = generate_password_hash(new_password)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Users SET password_hash = ? WHERE id = ?",
            (hashed, user_id)
        )
        conn.commit()
        conn.close()

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
