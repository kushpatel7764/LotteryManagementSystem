"""
This module provides decorators for Flask routes and database operations.

Includes:
- get_db_cursor: A context manager for safe SQLite database operations.
- admin_required: A route decorator that enforces admin or default_admin role.
"""

import sqlite3
from contextlib import contextmanager
from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


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


def admin_required(f):
    """
    Route decorator that restricts access to admin and default_admin roles.

    Redirects to the login page with an error flash if the current user
    does not hold an admin role.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Lazy import avoids a circular dependency: user_model imports get_db_cursor
        # from this module, so a top-level import of User here would be circular.
        from lottery_app.database.user_model import User  # pylint: disable=import-outside-toplevel
        user = User.get_by_id(current_user.id)
        if user is None or user.role not in ("admin", "default_admin"):
            flash("Unauthorized", "error")
            return redirect(url_for("security.login"))
        return f(*args, **kwargs)
    return decorated
