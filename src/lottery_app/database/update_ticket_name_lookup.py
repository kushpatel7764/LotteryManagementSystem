"""
Database management module for the TicketNameLookup table in lottery database system.
"""

import sqlite3

from lottery_app.database.setup_database import initialize_database
from lottery_app.decorators import get_db_cursor


def insert_ticket_name(database_path, ticket_name, ticket_gamenumber):
    """
    Inserts a new ticket name and its corresponding game number into the TicketNameLookup table.

    Parameters:
        database_path (str): Path to the SQLite database.
        ticket_name (str): The name of the ticket.
        ticket_gamenumber (str or int): The game number associated with the ticket.

    Returns:
        tuple:
            - ("Ticket Name insertion error: <error>", "error") on failure.

    Description:
        Adds a new entry mapping a ticket's game number to its name.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
                INSERT INTO TicketNameLookup (GameNumber, TicketName)
                VALUES (?, ?)
            """,
                (ticket_gamenumber, ticket_name),
            )
    except sqlite3.Error as e:
        return "Ticket Name insertion error: ".upper() + f"{e}", "error"

    return "SUCCESSFULLY UPDATED TICKET NAME TABLE", "success"
