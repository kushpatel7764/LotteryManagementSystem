"""
This module provides decorators for Flask routes and database operations.

Includes:
- with_error_handling: A decorator to handle view errors and render templates with fallback context.
- get_db_cursor: A context manager for safe SQLite database operations.
"""

import sqlite3
from contextlib import contextmanager
from functools import wraps

from flask import render_template


def with_error_handling(template_name, fallback_context=None):
    """
    Decorator to handle errors in Flask view functions and render a fallback template.

    Args:
        template_name (str): The template to render in case of an error.
        fallback_context (dict, optional): Additional context to pass to the template.

    Returns:
        function: Wrapped view function with error handling.
    """
    def decorator(view_func):

        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            try:
                context = view_func(*args, **kwargs)
                if isinstance(context, dict):
                    return render_template(template_name, **context)
                return context  # e.g., redirect
            except ValueError as ve:
                context = {"message": str(ve), "message_type": "error"}
                if fallback_context:
                    context.update(fallback_context)
                return render_template(template_name, **context)

        return wrapped_view

    return decorator


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
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
