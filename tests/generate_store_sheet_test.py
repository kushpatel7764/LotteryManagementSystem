"""Tests for the store sheet PDF generator."""
from lottery_app import generate_store_sheet


def _book(price, game, open_num, close_num, sold):
    return {
        "TicketName": "Test",
        "Ticket_GameNumber": game,
        "ActiveBookID": "000001",
        "TicketPrice": price,
        "Open": open_num,
        "Close": close_num,
        "Sold": sold,
    }


DAILY_REPORT = {
    "InstantTicketSold": 794,
    "OnlineTicketSold": 395,
    "InstantTicketCashed": 606,
    "OnlineTicketCashed": 597,
    "CashOnHand": 0,
    "TotalDue": -14,
}


def test_generates_pdf(tmp_path):
    """A normal day's books produce a non-empty PDF."""
    path = tmp_path / "sheet.pdf"
    log = [_book(50.0, "553", 39, 37, 2), _book(2.0, "543", 3, 1, 2)]
    generate_store_sheet.generate_store_sheet_pdf(
        str(path), {"Business Name": "Test Store"}, log, DAILY_REPORT
    )
    assert path.read_bytes().startswith(b"%PDF")


def test_handles_none_log_and_odd_prices(tmp_path):
    """A missing log, or prices outside the paper form, still produce a PDF."""
    path = tmp_path / "sheet.pdf"
    generate_store_sheet.generate_store_sheet_pdf(str(path), {}, None, {})
    assert path.exists()

    log = [_book(3.0, "600", 10, 8, 2), _book(2.5, "601", 5, 5, 0)]
    generate_store_sheet.generate_store_sheet_pdf(str(path), {}, log, DAILY_REPORT)
    assert path.exists()


def test_table_grows_past_default_rows():
    """More $50 books than printed rows grows the $50 table to fit them all."""
    books = {50: [_book(50.0, "490", 49, 49, 0)] * 12}
    columns = generate_store_sheet._layout_columns(  # pylint: disable=protected-access
        books, generate_store_sheet._STANDARD_PRICES  # pylint: disable=protected-access
    )
    fifty = next(b for b in columns[0] if b.get("price") == 50)
    assert fifty["slots"] == 12


def test_crowded_column_trims_blank_rows():
    """A column that would run off the page loses blank rows, never book rows."""
    books = {10: [_book(10.0, "552", 31, 30, 1)] * 22}
    columns = generate_store_sheet._layout_columns(  # pylint: disable=protected-access
        books, generate_store_sheet._STANDARD_PRICES  # pylint: disable=protected-access
    )
    ten = next(b for b in columns[1] if b.get("price") == 10)
    assert 22 <= ten["slots"] <= 28


def test_format_money():
    """Negative and fractional amounts format like the paper form."""
    fmt = generate_store_sheet._format_money  # pylint: disable=protected-access
    assert fmt(-14) == "-$14"
    assert fmt(1189) == "$1,189"
    assert fmt(2.5) == "$2.50"
