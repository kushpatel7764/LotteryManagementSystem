import sqlite3
from contextlib import contextmanager
from functools import wraps
from flask import render_template




def with_error_handling(template_name, fallback_context=None):
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
    Context manager that yields a cursor and ensures the connection is closed.
    Automatically commits changes if no exceptions occur.
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
