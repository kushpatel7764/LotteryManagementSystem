import sqlite3
from contextlib import contextmanager

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
