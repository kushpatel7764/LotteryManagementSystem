from lottery_app.database.update_ticket_name_lookup import insert_ticket_name
from lottery_app.decorators import get_db_cursor
import sqlite3


def test_insert_ticket_name_success(temp_db):
    msg, status = insert_ticket_name(
        temp_db, ticket_name="Mega Millions", ticket_gamenumber="MM01"
    )

    assert status == "success"

    with get_db_cursor(temp_db) as cursor:
        cursor.execute(
            "SELECT TicketName FROM TicketNameLookup WHERE GameNumber='MM01';"
        )
        assert cursor.fetchone()[0] == "Mega Millions"
        
def test_insert_ticket_name_sql_error(monkeypatch, temp_db):
    def bad_cursor(*args, **kwargs):
        raise sqlite3.Error("boom")

    monkeypatch.setattr(
        "lottery_app.database.update_ticket_name_lookup.get_db_cursor",
        bad_cursor,
    )

    msg, status = insert_ticket_name(temp_db, "Bad", "X")
    assert status == "error"