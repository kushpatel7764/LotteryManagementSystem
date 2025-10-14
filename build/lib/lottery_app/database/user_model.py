from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from lottery_app.utils.config import db_path
import sqlite3

DATABASE = db_path # Update with your actual db path

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return User(*row) if row else None

    @staticmethod
    def get_by_id(user_id):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return User(*row) if row else None

    @staticmethod
    def create(username, password):
        hashed = generate_password_hash(password)
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()
        conn.close()

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
