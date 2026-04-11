"""Tests for lottery_app.database.setup_database."""

import sqlite3

from lottery_app.database.setup_database import initialize_database


def test_setup_database_schema_creates_tables(db_cursor):
    """Test that initializing the database creates the expected tables."""
    tables = db_cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table'
    """).fetchall()
    table_names = {row["name"] for row in tables}

    # Adjust if your schema differs
    assert "Books" in table_names
    assert "ActivatedBooks" in table_names


def test_initialize_database_existing_file(db_path):
    """Test that calling initialize_database on an existing file is idempotent."""
    initialize_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    assert cursor.fetchall()

    conn.close()
