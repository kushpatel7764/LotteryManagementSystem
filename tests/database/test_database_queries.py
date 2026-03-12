import pytest
import sqlite3
from unittest.mock import patch, MagicMock

import lottery_app.database.database_queries as dq


@pytest.fixture
def mock_cursor():
    return MagicMock()


@pytest.fixture
def mock_cursor_ctx(mock_cursor):
    ctx = MagicMock()
    ctx.__enter__.return_value = mock_cursor
    ctx.__exit__.return_value = False
    return ctx


# get_books()
@patch("lottery_app.database.database_queries.setup_database.initialize_database")
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_books_success(mock_cursor_ctx, mock_init, mock_cursor):

    mock_cursor.fetchall.return_value = [
        ("B1", "100", False, 300, 10, "c", "u")
    ]

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_books("db")

    assert isinstance(result, list)
    assert result[0]["BookID"] == "B1"


@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_books_empty(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchall.return_value = []

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_books("db")

    assert result[1] == "error"

# count_activated_books()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_count_activated_books(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = (5,)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.count_activated_books("db")

    assert result == 5

# get_activated_books()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_activated_books_success(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchall.return_value = [
        (1, "BOOK1", "x", 5, 10)
    ]

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_activated_books("db")

    assert result[0]["ActiveBookID"] == "BOOK1"

# is_book()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_is_book_true(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = ("row",)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.is_book("db", "B1")

    assert result is True


@patch("lottery_app.database.database_queries.get_db_cursor")
def test_is_book_false(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = None
    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.is_book("db", "B1")

    assert result is False
    
# is_activated_book()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_is_activated_book_true(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = ("row",)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.is_activated_book("db", "AB1")

    assert result is True

# get_activated_book_is_at_ticketnumber()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_activated_book_is_at_ticketnumber(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = (42,)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_activated_book_is_at_ticketnumber("db", "AB1")

    assert result == 42
    
# get_activated_book()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_activated_book(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = ("row",)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_activated_book("db", "AB1")

    assert result == ("row",)
    
# get_book()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_book(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = ("row",)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_book("db", "B1")

    assert result == ("row",)
    
# get_all_active_book_ids()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_all_active_book_ids(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchall.return_value = [("A1",), ("A2",)]

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_all_active_book_ids("db")

    assert result == ["A1", "A2"]

# is_counting_ticket_number_set()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_is_counting_ticket_number_set_true(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = (10,)
    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    assert dq.is_counting_ticket_number_set("db", "AB1") is True
    
# get_all_instant_tickets_sold_quantity()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_all_instant_tickets_sold_quantity(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchall.return_value = [
        ("AB1", 5, 10)
    ]

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_all_instant_tickets_sold_quantity("db", "1")

    assert result[0]["ActiveBookID"] == "AB1"

# is_sold()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_is_sold(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = (True,)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    assert dq.is_sold("db", "B1") is True

# next_report_id()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_next_report_id(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = ("5",)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.next_report_id("db")

    assert result == "6"

# get_game_num_of()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_game_num_of(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchone.return_value = (123,)

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_game_num_of("db", "B1")

    assert result == 123
    
# can_submit()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_can_submit_true(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchall.return_value = [(1,), (2,)]

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    assert dq.can_submit("db") is True
    
# was_activated()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_was_activated(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchall.return_value = [(50,), (40,)]

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.was_activated("db", "B1")

    assert result == 50

# get_all_users()
@patch("lottery_app.database.database_queries.get_db_cursor")
def test_get_all_users(mock_cursor_ctx, mock_cursor):

    mock_cursor.fetchall.return_value = [
        ("kush", "admin"),
        ("bob", "standard")
    ]

    mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor

    result = dq.get_all_users("db")

    assert result[0]["username"] == "kush"

# get_ticket_with_bookid()
import pytest
from unittest.mock import patch, MagicMock

from lottery_app.database.database_queries import get_ticket_with_bookid


# --------------------------
# Success: ticket found
# --------------------------

@patch("lottery_app.database.database_queries.get_db_cursor")
@patch("lottery_app.database.database_queries.setup_database.initialize_database")
def test_get_ticket_with_bookid_found(mock_init_db, mock_get_cursor):

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ("SCAN1", "1", "BOOK1", 25)

    mock_get_cursor.return_value.__enter__.return_value = mock_cursor

    result = get_ticket_with_bookid("test.db", "BOOK1")

    assert result == ("SCAN1", "1", "BOOK1", 25)

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM TicketTimeLine WHERE BookID = ? LIMIT 1;", ("BOOK1",)
    )


# --------------------------
# Success: ticket NOT found
# --------------------------

@patch("lottery_app.database.database_queries.get_db_cursor")
@patch("lottery_app.database.database_queries.setup_database.initialize_database")
def test_get_ticket_with_bookid_not_found(mock_init_db, mock_get_cursor):

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None

    mock_get_cursor.return_value.__enter__.return_value = mock_cursor

    result = get_ticket_with_bookid("test.db", "BOOK99")

    assert result is None


# --------------------------
# ValueError handling
# --------------------------

@patch("lottery_app.database.database_queries.get_db_cursor")
@patch("lottery_app.database.database_queries.setup_database.initialize_database")
def test_get_ticket_with_bookid_value_error(mock_init_db, mock_get_cursor):

    mock_get_cursor.side_effect = ValueError("bad value")

    result = get_ticket_with_bookid("test.db", "BOOK1")

    assert result[1] == "error"
    assert "ERROR FETCHING TICKET TIMELINE" in result[0]


# --------------------------
# TypeError handling
# --------------------------

@patch("lottery_app.database.database_queries.get_db_cursor")
@patch("lottery_app.database.database_queries.setup_database.initialize_database")
def test_get_ticket_with_bookid_type_error(mock_init_db, mock_get_cursor):

    mock_get_cursor.side_effect = TypeError("bad type")

    result = get_ticket_with_bookid("test.db", "BOOK1")

    assert result[1] == "error"
    assert "ERROR FETCHING TICKET TIMELINE" in result[0]
    
# get_scan_ticket_page_table(db)
from lottery_app.database.database_queries import get_scan_ticket_page_table


@pytest.fixture
def test_db(tmp_path):
    """Creates a temporary SQLite database with required tables."""
    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE ActivatedBooks (
            ActiveBookID TEXT PRIMARY KEY,
            isAtTicketNumber INTEGER,
            countingTicketNumber INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE Books (
            BookID TEXT PRIMARY KEY,
            TicketPrice INTEGER,
            GameNumber INTEGER,
            Is_Sold INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE TicketNameLookup (
            GameNumber INTEGER PRIMARY KEY,
            TicketName TEXT
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_scan_ticket_page_table_success(test_db):

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO ActivatedBooks VALUES ('BOOK1', 10, 20)"
    )

    cursor.execute(
        "INSERT INTO Books VALUES ('BOOK1', 30, 1001, 0)"
    )

    cursor.execute(
        "INSERT INTO TicketNameLookup VALUES (1001, 'Lucky 7s')"
    )

    conn.commit()
    conn.close()

    result = get_scan_ticket_page_table(test_db)

    assert isinstance(result, list)
    assert len(result) == 1

    row = result[0]

    assert row["TicketName"] == "Lucky 7s"
    assert row["ActiveBookID"] == "BOOK1"
    assert row["ticketPrice"] == 30
    assert row["GameNumber"] == 1001
    assert row["Is_Sold"] == 0
    assert row["isAtTicketNumber"] == 10
    assert row["countingTicketNumber"] == 20
    
def test_get_scan_ticket_page_table_empty(test_db):

    result = get_scan_ticket_page_table(test_db)

    assert result == []
    
def test_get_scan_ticket_page_table_sorting(test_db):

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO ActivatedBooks VALUES ('BOOK1', 1, 2)")
    cursor.execute("INSERT INTO ActivatedBooks VALUES ('BOOK2', 3, 4)")

    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 10, 1001, 0)")
    cursor.execute("INSERT INTO Books VALUES ('BOOK2', 50, 1002, 0)")

    cursor.execute("INSERT INTO TicketNameLookup VALUES (1001, 'Cheap Ticket')")
    cursor.execute("INSERT INTO TicketNameLookup VALUES (1002, 'Expensive Ticket')")

    conn.commit()
    conn.close()

    result = get_scan_ticket_page_table(test_db)

    assert len(result) == 2

    # Should be sorted by TicketPrice DESC
    assert result[0]["ticketPrice"] == 50
    assert result[1]["ticketPrice"] == 10
    
def test_get_scan_ticket_page_table_missing_ticket_name(test_db):

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO ActivatedBooks VALUES ('BOOK1', 1, 2)")
    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 20, 9999, 0)")

    conn.commit()
    conn.close()

    result = get_scan_ticket_page_table(test_db)

    assert len(result) == 1
    assert result[0]["TicketName"] is None

from unittest.mock import patch


def test_get_scan_ticket_page_table_database_error(test_db):
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_cursor
    mock_context_manager.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context_manager
    ):
        result = get_scan_ticket_page_table(test_db)

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "DATABASE ERROR IN get_scan_ticket_page_table" in result[0]
    
# get_all_sold_books
from lottery_app.database.database_queries import get_all_sold_books

@pytest.fixture
def test_db_get_all_sold_books(tmp_path):
    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE Books (
            BookID TEXT PRIMARY KEY,
            TicketPrice INTEGER,
            Is_Sold BOOLEAN
        )
    """)

    cursor.execute("""
        CREATE TABLE SalesLog (
            ActiveBookID TEXT,
            Ticket_Sold_Quantity INTEGER,
            ReportID INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_all_sold_books_success(test_db_get_all_sold_books):

    conn = sqlite3.connect(test_db_get_all_sold_books)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 10, True)")
    cursor.execute("INSERT INTO SalesLog VALUES ('BOOK1', 50, 1)")

    conn.commit()
    conn.close()

    result = get_all_sold_books(test_db_get_all_sold_books, 1)

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["BookID"] == "BOOK1"
    
def test_get_all_sold_books_multiple(test_db_get_all_sold_books):

    conn = sqlite3.connect(test_db_get_all_sold_books)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 10, True)")
    cursor.execute("INSERT INTO Books VALUES ('BOOK2', 20, True)")

    cursor.execute("INSERT INTO SalesLog VALUES ('BOOK1', 30, 1)")
    cursor.execute("INSERT INTO SalesLog VALUES ('BOOK2', 40, 1)")

    conn.commit()
    conn.close()

    result = get_all_sold_books(test_db_get_all_sold_books, 1)

    assert len(result) == 2

    ids = {row["BookID"] for row in result}

    assert "BOOK1" in ids
    assert "BOOK2" in ids
    
def test_get_all_sold_books_none_found(test_db_get_all_sold_books):

    conn = sqlite3.connect(test_db_get_all_sold_books)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 10, True)")
    cursor.execute("INSERT INTO SalesLog VALUES ('BOOK1', 30, 2)")  # different report

    conn.commit()
    conn.close()

    result = get_all_sold_books(test_db_get_all_sold_books, 1)

    assert result == []

def test_get_all_sold_books_not_sold_filtered(test_db_get_all_sold_books):

    conn = sqlite3.connect(test_db_get_all_sold_books)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 10, False)")
    cursor.execute("INSERT INTO SalesLog VALUES ('BOOK1', 30, 1)")

    conn.commit()
    conn.close()

    result = get_all_sold_books(test_db_get_all_sold_books, 1)

    assert result == []
    
def test_get_all_sold_books_database_error(test_db_get_all_sold_books):

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_cursor
    mock_context.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context
    ):
        result = get_all_sold_books(test_db_get_all_sold_books, 1)

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "DATABASE ERROR IN get_all_sold_books" in result[0]
    
# get_table_for_invoice

from lottery_app.database.database_queries import get_table_for_invoice

@pytest.fixture
def test_db_get_table_for_invoice(tmp_path):
    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE Books(
            BookID TEXT PRIMARY KEY,
            TicketPrice INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE SalesLog(
            Ticket_Name TEXT,
            Ticket_GameNumber INTEGER,
            ActiveBookID TEXT,
            prev_TicketNum INTEGER,
            current_TicketNum INTEGER,
            Ticket_Sold_Quantity INTEGER,
            ReportID INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_table_for_invoice_success(test_db_get_table_for_invoice):

    conn = sqlite3.connect(test_db_get_table_for_invoice)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 20)")

    cursor.execute("""
        INSERT INTO SalesLog
        VALUES ('Lucky 7s', 1001, 'BOOK1', 0, 10, 10, 1)
    """)

    conn.commit()
    conn.close()

    result = get_table_for_invoice(test_db_get_table_for_invoice, 1)

    assert isinstance(result, list)
    assert len(result) == 1

    row = result[0]

    assert row["TicketName"] == "Lucky 7s"
    assert row["Ticket_GameNumber"] == 1001
    assert row["ActiveBookID"] == "BOOK1"
    assert row["TicketPrice"] == 20
    assert row["Open"] == 0
    assert row["Close"] == 10
    assert row["Sold"] == 10
    
def test_get_table_for_invoice_multiple_rows(test_db_get_table_for_invoice):

    conn = sqlite3.connect(test_db_get_table_for_invoice)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 10)")
    cursor.execute("INSERT INTO Books VALUES ('BOOK2', 50)")

    cursor.execute("""
        INSERT INTO SalesLog VALUES ('TicketA',1001,'BOOK1',0,5,5,1)
    """)

    cursor.execute("""
        INSERT INTO SalesLog VALUES ('TicketB',1002,'BOOK2',0,10,10,1)
    """)

    conn.commit()
    conn.close()

    result = get_table_for_invoice(test_db_get_table_for_invoice, 1)

    assert len(result) == 2
    
def test_get_table_for_invoice_sorted_by_price(test_db_get_table_for_invoice):

    conn = sqlite3.connect(test_db_get_table_for_invoice)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO Books VALUES ('BOOK1', 10)")
    cursor.execute("INSERT INTO Books VALUES ('BOOK2', 50)")

    cursor.execute("""
        INSERT INTO SalesLog VALUES ('CheapTicket',1001,'BOOK1',0,5,5,1)
    """)

    cursor.execute("""
        INSERT INTO SalesLog VALUES ('ExpensiveTicket',1002,'BOOK2',0,10,10,1)
    """)

    conn.commit()
    conn.close()

    result = get_table_for_invoice(test_db_get_table_for_invoice, 1)

    assert result[0]["TicketPrice"] == 50
    assert result[1]["TicketPrice"] == 10
    
def test_get_table_for_invoice_no_rows(test_db_get_table_for_invoice):

    result = get_table_for_invoice(test_db_get_table_for_invoice, 99)

    assert result == []
    
def test_get_table_for_invoice_database_error(test_db_get_table_for_invoice):

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_cursor
    mock_context.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context
    ):
        result = get_table_for_invoice(test_db_get_table_for_invoice, 1)

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "DATABASE ERROR IN get_table_for_invoice" in result[0]

# get_daily_report

from lottery_app.database.database_queries import get_daily_report

@pytest.fixture
def test_db_get_daily_report(tmp_path):

    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE SaleReport(
            ReportID INTEGER,
            ReportDate TEXT,
            ReportTime TEXT,
            InstantTicketSold INTEGER,
            OnlineTicketSold INTEGER,
            InstantTicketCashed INTEGER,
            OnlineTicketCashed INTEGER,
            CashOnHand INTEGER,
            TotalDue INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_daily_report_success(test_db_get_daily_report):

    conn = sqlite3.connect(test_db_get_daily_report)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SaleReport
        VALUES (1,'2026-03-10','12:00',10,20,5,2,300,150)
    """)

    conn.commit()
    conn.close()

    result = get_daily_report(test_db_get_daily_report, 1)

    assert isinstance(result, dict)

    assert result["ReportID"] == 1
    assert result["ReportDate"] == "2026-03-10"
    assert result["ReportTime"] == "12:00"
    assert result["InstantTicketSold"] == 10
    assert result["OnlineTicketSold"] == 20
    assert result["InstantTicketCashed"] == 5
    assert result["OnlineTicketCashed"] == 2
    assert result["CashOnHand"] == 300
    assert result["TotalDue"] == 150

def test_get_daily_report_not_found(test_db_get_daily_report):

    result = get_daily_report(test_db_get_daily_report, 99)

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "NO DAILY REPORT FOUND FOR ReportID(99)" in result[0]
    
def test_get_daily_report_database_error(test_db_get_daily_report):

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_cursor
    mock_context.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context
    ):
        result = get_daily_report(test_db_get_daily_report, 1)

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "DATABASE ERROR IN get_daily_report" in result[0]
    
# get_all_sales_reports

from lottery_app.database.database_queries import get_all_sales_reports

@pytest.fixture
def test_db_get_all_sales_reports(tmp_path):

    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE SaleReport(
            ReportID TEXT,
            ReportDate TEXT,
            ReportTime TEXT,
            InstantTicketSold INTEGER,
            OnlineTicketSold INTEGER,
            InstantTicketCashed INTEGER,
            OnlineTicketCashed INTEGER,
            CashOnHand INTEGER,
            TotalDue INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_all_sales_reports_single(test_db_get_all_sales_reports):

    conn = sqlite3.connect(test_db_get_all_sales_reports)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SaleReport
        VALUES ('1','2026-03-10','12:00',10,20,5,2,300,150)
    """)

    conn.commit()
    conn.close()

    result = get_all_sales_reports(test_db_get_all_sales_reports)

    assert isinstance(result, list)
    assert len(result) == 1

    report = result[0]

    assert report["ReportID"] == "1"
    assert report["ReportDate"] == "2026-03-10"
    assert report["ReportTime"] == "12:00"
    assert report["InstantTicketSold"] == 10
    assert report["OnlineTicketSold"] == 20
    assert report["InstantTicketCashed"] == 5
    assert report["OnlineTicketCashed"] == 2
    assert report["CashOnHand"] == 300
    assert report["TotalDue"] == 150
    
def test_get_all_sales_reports_multiple(test_db_get_all_sales_reports):

    conn = sqlite3.connect(test_db_get_all_sales_reports)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SaleReport VALUES ('1','2026-03-10','12:00',1,1,1,1,100,50)
    """)

    cursor.execute("""
        INSERT INTO SaleReport VALUES ('2','2026-03-11','13:00',2,2,2,2,200,100)
    """)

    conn.commit()
    conn.close()

    result = get_all_sales_reports(test_db_get_all_sales_reports)

    assert len(result) == 2
    
def test_get_all_sales_reports_sorted_desc(test_db_get_all_sales_reports):

    conn = sqlite3.connect(test_db_get_all_sales_reports)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SaleReport VALUES ('1','2026-03-10','12:00',1,1,1,1,100,50)
    """)

    cursor.execute("""
        INSERT INTO SaleReport VALUES ('10','2026-03-11','13:00',2,2,2,2,200,100)
    """)

    cursor.execute("""
        INSERT INTO SaleReport VALUES ('3','2026-03-12','14:00',3,3,3,3,300,150)
    """)

    conn.commit()
    conn.close()

    result = get_all_sales_reports(test_db_get_all_sales_reports)

    assert result[0]["ReportID"] == "10"
    assert result[1]["ReportID"] == "3"
    assert result[2]["ReportID"] == "1"
    
def test_get_all_sales_reports_empty(test_db_get_all_sales_reports):

    result = get_all_sales_reports(test_db_get_all_sales_reports)

    assert result == []

def test_get_all_sales_reports_database_error(test_db_get_all_sales_reports):

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_cursor
    mock_context.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context
    ):
        with pytest.raises(RuntimeError) as excinfo:
            get_all_sales_reports(test_db_get_all_sales_reports)

    assert "DATABASE ERROR IN get_all_sales_reports" in str(excinfo.value)
    
# get_sales_log

from lottery_app.database.database_queries import get_sales_log

@pytest.fixture
def test_db_get_sales_log(tmp_path):

    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE SalesLog(
            id INTEGER,
            ReportID INTEGER,
            dummy TEXT,
            ActiveBookID TEXT,
            prev_TicketNum INTEGER,
            current_TicketNum INTEGER,
            Ticket_Sold_Quantity INTEGER,
            Ticket_Name TEXT,
            Ticket_GameNumber INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_sales_log_success(test_db_get_sales_log):

    conn = sqlite3.connect(test_db_get_sales_log)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SalesLog
        VALUES (1,1,'x','BOOK1',0,10,10,'Lucky 7s',1001)
    """)

    conn.commit()
    conn.close()

    result = get_sales_log(test_db_get_sales_log, 1)

    assert isinstance(result, list)
    assert len(result) == 1

    row = result[0]

    assert row["ActiveBookID"] == "BOOK1"
    assert row["Open"] == 0
    assert row["Close"] == 10
    assert row["Sold"] == 10
    assert row["Game Name"] == "Lucky 7s"
    assert row["Game #"] == 1001
    
def test_get_sales_log_multiple_rows(test_db_get_sales_log):

    conn = sqlite3.connect(test_db_get_sales_log)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SalesLog VALUES (1,1,'x','BOOK1',0,5,5,'GameA',1001)
    """)

    cursor.execute("""
        INSERT INTO SalesLog VALUES (2,1,'x','BOOK2',0,10,10,'GameB',1002)
    """)

    conn.commit()
    conn.close()

    result = get_sales_log(test_db_get_sales_log, 1)

    assert len(result) == 2

    ids = {row["ActiveBookID"] for row in result}

    assert "BOOK1" in ids
    assert "BOOK2" in ids
    
def test_get_sales_log_empty(test_db_get_sales_log):

    result = get_sales_log(test_db_get_sales_log, 99)

    assert result == []

def test_get_sales_log_column_mapping(test_db_get_sales_log):

    conn = sqlite3.connect(test_db_get_sales_log)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SalesLog
        VALUES (5,2,'x','BOOK5',20,30,10,'Mega Millions',2000)
    """)

    conn.commit()
    conn.close()

    result = get_sales_log(test_db_get_sales_log, 2)

    row = result[0]

    assert row == {
        "ActiveBookID": "BOOK5",
        "Open": 20,
        "Close": 30,
        "Sold": 10,
        "Game Name": "Mega Millions",
        "Game #": 2000
    }

def test_get_sales_log_database_error(test_db_get_sales_log):

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_cursor
    mock_context.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context
    ):
        result = get_sales_log(test_db_get_sales_log, 1)

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "Database ERROR IN get_sales_log" in result[0]

# get_sales_log_with_bookid

from lottery_app.database.database_queries import get_sales_log_with_bookid

@pytest.fixture
def test_db_get_sales_log(tmp_path):
    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE SalesLog(
            id INTEGER,
            ReportID INTEGER,
            dummy TEXT,
            ActiveBookID TEXT,
            prev_TicketNum INTEGER,
            current_TicketNum INTEGER,
            Ticket_Sold_Quantity INTEGER,
            Ticket_Name TEXT,
            Ticket_GameNumber INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_sales_log_with_bookid_success(test_db_get_sales_log):

    conn = sqlite3.connect(test_db_get_sales_log)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SalesLog
        VALUES (1,1,'x','BOOK123',0,20,20,'Lucky 7s',1001)
    """)

    conn.commit()
    conn.close()

    result = get_sales_log_with_bookid(test_db_get_sales_log, 1, "BOOK123")

    assert isinstance(result, dict)

    assert result["ActiveBookID"] == "BOOK123"
    assert result["Open"] == 0
    assert result["Close"] == 20
    assert result["Sold"] == 20
    assert result["Game Name"] == "Lucky 7s"
    assert result["Game #"] == 1001
    
def test_get_sales_log_with_bookid_mapping(test_db_get_sales_log):

    conn = sqlite3.connect(test_db_get_sales_log)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO SalesLog
        VALUES (5,2,'x','BOOK5',10,30,20,'Mega Millions',2000)
    """)

    conn.commit()
    conn.close()

    result = get_sales_log_with_bookid(test_db_get_sales_log, 2, "BOOK5")

    assert result == {
        "ActiveBookID": "BOOK5",
        "Open": 10,
        "Close": 30,
        "Sold": 20,
        "Game Name": "Mega Millions",
        "Game #": 2000
    }

def test_get_sales_log_with_bookid_not_found(test_db_get_sales_log):

    result = get_sales_log_with_bookid(test_db_get_sales_log, 99, "BOOK999")

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "NO ENTRY FOUND FOR REPORTID 99 AND BOOKID BOOK999" in result[0]

def test_get_sales_log_with_bookid_database_error(test_db_get_sales_log):

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_cursor
    mock_context.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context
    ):
        result = get_sales_log_with_bookid(test_db_get_sales_log, 1, "BOOK1")

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "DATABASE ERROR IN get_sales_log_with_bookid" in result[0]

# get_gm_from_lookup

from lottery_app.database.database_queries import get_gm_from_lookup

@pytest.fixture
def test_db_get_gm_from_lookup(tmp_path):
    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE TicketNameLookup(
            GameNumber INTEGER
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_gm_from_lookup_multiple(test_db_get_gm_from_lookup):

    conn = sqlite3.connect(test_db_get_gm_from_lookup)
    cursor = conn.cursor()

    cursor.executemany(
        "INSERT INTO TicketNameLookup VALUES (?)",
        [(1001,), (1002,), (1003,)]
    )

    conn.commit()
    conn.close()

    result = get_gm_from_lookup(test_db_get_gm_from_lookup)

    assert isinstance(result, set)
    assert result == {1001, 1002, 1003}

def test_get_gm_from_lookup_single(test_db_get_gm_from_lookup):

    conn = sqlite3.connect(test_db_get_gm_from_lookup)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO TicketNameLookup VALUES (2000)"
    )

    conn.commit()
    conn.close()

    result = get_gm_from_lookup(test_db_get_gm_from_lookup)

    assert result == {2000}

def test_get_gm_from_lookup_empty(test_db_get_gm_from_lookup):

    result = get_gm_from_lookup(test_db_get_gm_from_lookup)

    assert result == set()

def test_get_gm_from_lookup_removes_duplicates(test_db_get_gm_from_lookup):

    conn = sqlite3.connect(test_db_get_gm_from_lookup)
    cursor = conn.cursor()

    cursor.executemany(
        "INSERT INTO TicketNameLookup VALUES (?)",
        [(1001,), (1001,), (1002,)]
    )

    conn.commit()
    conn.close()

    result = get_gm_from_lookup(test_db_get_gm_from_lookup)

    assert result == {1001, 1002}

def test_get_gm_from_lookup_database_error(test_db_get_gm_from_lookup):

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_cursor
    mock_context.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context
    ):
        result = get_gm_from_lookup(test_db_get_gm_from_lookup)

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "DATABASE ERROR IN get_gm_from_lookup" in result[0]

# get_ticket_name

from lottery_app.database.database_queries import get_ticket_name

@pytest.fixture
def test_db_get_ticket_name(tmp_path):

    db_path = tmp_path / "test.db"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE TicketNameLookup(
            GameNumber INTEGER,
            TicketName TEXT
        )
    """)

    conn.commit()
    conn.close()

    return str(db_path)

def test_get_ticket_name_success(test_db_get_ticket_name):

    conn = sqlite3.connect(test_db_get_ticket_name)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO TicketNameLookup VALUES (?, ?)",
        (1001, "Lucky 7s")
    )

    conn.commit()
    conn.close()

    result = get_ticket_name(test_db_get_ticket_name, 1001)

    assert result == "Lucky 7s"

def test_get_ticket_name_not_found(test_db_get_ticket_name):

    result = get_ticket_name(test_db_get_ticket_name, 9999)

    assert result == "N/A"

def test_get_ticket_name_multiple_entries_returns_first(test_db_get_ticket_name):

    conn = sqlite3.connect(test_db_get_ticket_name)
    cursor = conn.cursor()

    cursor.executemany(
        "INSERT INTO TicketNameLookup VALUES (?, ?)",
        [
            (2000, "Mega Millions"),
            (2000, "Duplicate Name")
        ]
    )

    conn.commit()
    conn.close()

    result = get_ticket_name(test_db_get_ticket_name, 2000)

    assert result == "Mega Millions"

def test_get_ticket_name_database_error(test_db_get_ticket_name):

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB failure")

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_cursor
    mock_context.__exit__.return_value = False

    with patch(
        "lottery_app.database.database_queries.get_db_cursor",
        return_value=mock_context
    ):
        result = get_ticket_name(test_db_get_ticket_name, 1001)

    assert isinstance(result, tuple)
    assert result[1] == "error"
    assert "DATABASE ERROR IN get_ticket_name" in result[0]

