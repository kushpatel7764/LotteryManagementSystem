"""
Database setup module for the lottery database system.
"""

import os
from lottery_app.decorators import get_db_cursor
from lottery_app.utils.config import sql_file_path
from werkzeug.security import generate_password_hash


# Connect to database
def setup_database_schema_with_sql_file(cursor):
    """
    Executes an SQL schema script to set up or modify the structure of a SQLite database.

    Parameters:
        cursor (sqlite3.Cursor): The cursor object used to execute SQL commands.
        sql_filename (str): The filename of the SQL file containing the schema setup instructions.

    Description:
        This function locates the provided SQL file (assumed to be one directory above the script),
        reads its contents, and executes the SQL script using the given database cursor.
        After execution, it commits the changes to the database.
    """
    try:
        # sql_file_path = resource_path(sql_filename)

        # Read the SQL schema file
        with open(sql_file_path, "r", encoding="utf-8") as file:
            sql_script = file.read()
            cursor.executescript(sql_script)
    except Exception as e:
        print(f"Error setting up database schema: {e}")
        raise

def create_default_user(cursor):
        cursor.execute("""
            SELECT * FROM Users WHERE username = ?
            """, ("admin", ))
        if cursor.fetchone() is None:
            hashed = generate_password_hash("adminpass")
            cursor.execute("""
            INSERT INTO Users (username, password_hash, role) VALUES (?, ?, ?)
            """, ("admin", hashed, "default_admin"))

def initialize_database(db_path):
    """
    Initializes a new or existing SQLite database by setting up its schema.

    Parameters:
        database_path (str): The file path to the SQLite database file.
    """

    with get_db_cursor(db_path) as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        if not os.path.exists(db_path):
            # Database file not found
            return

        if not cursor.fetchall():
            print("Creating new database and schema...")
            # Pass the path through
            setup_database_schema_with_sql_file(cursor)
            create_default_user(cursor)
