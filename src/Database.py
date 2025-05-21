import os

# Connect to database
def setup_database_with_sql_file(cursor, conn, sql_filename):
    setup_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Moves up one level
    sql_file_path = os.path.join(setup_dir, sql_filename)

    # Read the SQL schema file
    with open(sql_file_path, "r") as file:
        sql_script = file.read()

    cursor.executescript(sql_script)
    conn.commit()