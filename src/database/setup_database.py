"""
Database setup module for the lottery database system.
"""

import os

from src.decorators import get_db_cursor


# Connect to database
def setup_database_schema_with_sql_file(cursor, sql_filename):
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
        setup_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        sql_file_path = os.path.join(setup_dir, sql_filename)

        # Read the SQL schema file
        with open(sql_file_path, "r", encoding="utf-8") as file:
            sql_script = file.read()

        cursor.executescript(sql_script)
    except Exception as e:
        print(f"Error setting up database schema: {e}")
        raise


def initialize_database(database_path):
    """
    Initializes a new or existing SQLite database by setting up its schema.

    Parameters:
        database_path (str): The file path to the SQLite database file.
    """

    with get_db_cursor(database_path) as cursor:
        setup_database_schema_with_sql_file(cursor, "Lottery_DB_Schema.sql")
