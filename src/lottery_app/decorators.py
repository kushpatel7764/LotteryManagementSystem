"""
This module provides decorators for Flask routes and database operations.

Includes:
- get_db_cursor: A context manager for safe SQLite database operations.
"""

import sqlite3
from contextlib import contextmanager


@contextmanager
def get_db_cursor(db_path):
    """
    Context manager for safely handling SQLite database connections.

    Args:
        db_path (str): Path to the SQLite database.

    Yields:
        sqlite3.Cursor: Cursor object for database operations.

    Raises:
        sqlite3.Error: If a database operation fails.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # ✅ ADD THIS
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
