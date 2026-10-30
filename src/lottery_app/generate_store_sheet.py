"""
Module for generating the store sheet.

The store sheet is the one-page paper form the store fills in by hand each day:
one table per ticket price ($50, $30, $20, $10, $5, $2, $1) listing every book's
game number, open/close ticket numbers and tickets sold, a calculations table
totalling sales by price, and a summary box with the amount due.

Tables grow to fit however many books are active, and rows are numbered
consecutively across all tables.
"""

import logging
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

_PAGE_WIDTH, _PAGE_HEIGHT = LETTER
_MARGIN_X = 25
_MARGIN_TOP = 28
_MARGIN_BOTTOM = 25
_COLUMN_GAP = 20
_COLUMN_WIDTH = (_PAGE_WIDTH - 2 * _MARGIN_X - 2 * _COLUMN_GAP) / 3
_ROW_HEIGHT = 12

# Space between stacked blocks in a column, in rows.
_BLOCK_GAP = 1.25
# Space above the summary box, in rows.
_SUMMARY_GAP = 2

# Printed row count per price table on the paper form; tables with more books grow.
_DEFAULT_SLOTS = {50: 10, 30: 10, 20: 15, 10: 28, 5: 26, 2: 24, 1: 16}
_STANDARD_PRICES = [50, 30, 20, 10, 5, 2, 1]
# Which column each price table lives in, matching the paper form.
_COLUMN_PRICES = [[50, 30, 20], [10, 5], [2, 1]]

# Relative column widths.
_TABLE_COLS = [0.16, 0.21, 0.21, 0.21, 0.21]
_CALC_COLS = [0.25, 0.40, 0.35]
_SUMMARY_WIDTH = 0.82
_SUMMARY_COLS = [0.62, 0.38]


def generate_store_sheet_pdf(filename, store_info, invoice_log, daily_report):
    """
    Generate the daily store sheet as a one-page PDF.

    Args:
        filename (str): Output PDF filename.
        store_info (dict): Store details; "Business Name" is printed in the header.
        invoice_log (list[dict]): Ticket sales records (see get_table_for_invoice).
        daily_report (dict): Daily financial summary including totals.

    Returns:
        None
    """
    if invoice_log is None:
        logger.error("Invoice log is None; generating an empty store sheet")
        invoice_log = []

    books_by_price = _group_by_price(invoice_log)
    prices = _STANDARD_PRICES + sorted(
        (p for p in books_by_price if p not in _STANDARD_PRICES), reverse=True
    )
    sold_by_price = {
        p: sum(_as_int(b["Sold"]) for b in books_by_price.get(p, [])) for p in prices
    }

    columns = _layout_columns(books_by_price, prices)
    header_rows = 2
    available = _PAGE_HEIGHT - _MARGIN_TOP - _MARGIN_BOTTOM
    tallest = max(_column_height(col) for col in columns) + header_rows
    row_height = min(_ROW_HEIGHT, available / tallest)

    c = canvas.Canvas(filename, pagesize=LETTER)
    y = _draw_header(c, store_info, row_height)

    row_numbers = {}
    next_number = 1
    for price in prices:
        row_numbers[price] = next_number
        next_number += len(books_by_price.get(price, []))

    for index, column in enumerate(columns):
        x = _MARGIN_X + index * (_COLUMN_WIDTH + _COLUMN_GAP)
        col_y = y
        for block in column:
            kind = block["kind"]
            if kind == "table":
                price = block["price"]
                col_y = _draw_price_table(
                    c, x, col_y, row_height, price,
                    books_by_price.get(price, []), block["slots"], row_numbers[price],
                )
            elif kind == "calc":
                col_y = _draw_calculations(c, x, col_y, row_height, prices, sold_by_price)
            elif kind == "summary":
                col_y -= _SUMMARY_GAP * row_height
                col_y = _draw_summary(c, x, col_y, row_height, daily_report)
            col_y -= _BLOCK_GAP * row_height

    c.save()


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _price_key(price):
    price = float(price or 0)
    return int(price) if price.is_integer() else price


def _format_price(price):
    return f"${price}" if isinstance(price, int) else f"${price:.2f}"


def _format_money(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    text = f"{amount:,.0f}" if amount.is_integer() else f"{amount:,.2f}"
    return f"{sign}${text}"


def _group_by_price(invoice_log):
    books_by_price = {}
    for log in invoice_log:
        books_by_price.setdefault(_price_key(log["TicketPrice"]), []).append(log)
    return books_by_price


def _layout_columns(books_by_price, prices):
    """
    Assign blocks to the three page columns and size each price table.

    A table gets the paper form's row count, or more if it has more books. When
    a column would run off the page, blank rows are trimmed from its emptiest
    tables first; anything still too tall is handled by shrinking row height.
    """
    extra_prices = [p for p in prices if p not in _STANDARD_PRICES]
    column_prices = [list(c) for c in _COLUMN_PRICES]
    column_prices[2].extend(extra_prices)

    columns = []
    for index, col_prices in enumerate(column_prices):
        column = []
        for price in col_prices:
            books = len(books_by_price.get(price, []))
            slots = max(_DEFAULT_SLOTS.get(price, 0), books, 1)
            column.append({"kind": "table", "price": price, "slots": slots, "books": books})
        if index == 0:
            column.append({"kind": "calc", "rows": len(prices) + 4})
        if index == 2:
            column.append({"kind": "summary", "rows": 5 + _SUMMARY_GAP})
        columns.append(column)

    available_rows = (_PAGE_HEIGHT - _MARGIN_TOP - _MARGIN_BOTTOM) / _ROW_HEIGHT - 2
    for column in columns:
        tables = [b for b in column if b["kind"] == "table"]
        while _column_height(column) > available_rows:
            roomiest = max(tables, key=lambda b: b["slots"] - max(b["books"], 1))
            if roomiest["slots"] <= max(roomiest["books"], 1):
                break
            roomiest["slots"] -= 1
    return columns


def _column_height(column):
    """Height of a column in rows: header and total row per table, plus gaps."""
    height = 0
    for block in column:
        height += block["slots"] + 2 if block["kind"] == "table" else block["rows"]
    return height + _BLOCK_GAP * (len(column) - 1)


def _font_size(row_height):
    return max(5.0, min(8.5, row_height * 0.7))


def _draw_row(c, x, y, row_height, widths, cells, aligns, bold=None):
    """Draw one bordered row of cells with its top edge at y. Returns the next y."""
    size = _font_size(row_height)
    baseline = y - row_height + (row_height - size) / 2 + size * 0.2
    cell_x = x
    for i, (width, text) in enumerate(zip(widths, cells)):
        c.rect(cell_x, y - row_height, width, row_height)
        if text not in (None, ""):
            c.setFont("Helvetica-Bold" if bold and bold[i] else "Helvetica", size)
            if aligns[i] == "left":
                c.drawString(cell_x + 2.5, baseline, str(text))
            else:
                c.drawCentredString(cell_x + width / 2, baseline, str(text))
        cell_x += width
    return y - row_height


def _draw_header(c, store_info, row_height):
    width = _PAGE_WIDTH - 2 * _MARGIN_X
    y = _PAGE_HEIGHT - _MARGIN_TOP
    size = _font_size(row_height) + 0.5
    c.setLineWidth(0.6)
    for text_left, text_right in (
        ("Shri Ganeshaya Namah", f"Date: {datetime.now().strftime('%m/%d/%Y')}"),
        (store_info.get("Business Name", ""), ""),
    ):
        c.rect(_MARGIN_X, y - row_height, width, row_height)
        baseline = y - row_height + (row_height - size) / 2 + size * 0.2
        c.setFont("Helvetica", size)
        c.drawString(_MARGIN_X + 3, baseline, text_left)
        if text_right:
            c.drawRightString(_MARGIN_X + width - 8, baseline, text_right)
        y -= row_height
    return y


def _draw_price_table(c, x, y, row_height, price, books, slots, first_number):
    widths = [w * _COLUMN_WIDTH for w in _TABLE_COLS]
    aligns = ["left", "center", "center", "center", "center"]
    y = _draw_row(
        c, x, y, row_height, widths,
        [_format_price(price), "Game #", "Open", "Close", "Sell"], aligns,
    )
    for i in range(slots):
        if i < len(books):
            book = books[i]
            cells = [
                first_number + i,
                book["Ticket_GameNumber"],
                book["Open"],
                book["Close"],
                book["Sold"],
            ]
        else:
            cells = [""] * 5
        y = _draw_row(c, x, y, row_height, widths, cells, aligns)
    total = sum(_as_int(b["Sold"]) for b in books)
    return _draw_row(
        c, x, y, row_height, widths, ["Total", "", "", "", total], aligns,
        bold=[False, False, False, False, True],
    )


def _draw_calculations(c, x, y, row_height, prices, sold_by_price):
    widths = [w * _COLUMN_WIDTH for w in _CALC_COLS]
    center = ["center"] * 3
    calc_aligns = ["center", "left", "center"]
    y = _draw_row(c, x, y, row_height, [_COLUMN_WIDTH], ["Calculations"], ["center"])
    y = _draw_row(c, x, y, row_height, widths, ["Price", "# of Tickets", "Total"], center)
    total_tickets = 0
    total_amount = 0
    for price in prices:
        sold = sold_by_price[price]
        total_tickets += sold
        total_amount += price * sold
        y = _draw_row(
            c, x, y, row_height, widths,
            [_format_price(price), f"x  {sold}", _format_money(price * sold)], calc_aligns,
        )
    y = _draw_row(c, x, y, row_height, widths, ["", "", ""], center)
    return _draw_row(
        c, x, y, row_height, widths,
        ["Total", total_tickets, _format_money(total_amount)], calc_aligns,
        bold=[False, False, True],
    )


def _draw_summary(c, x, y, row_height, daily_report):
    box_width = _COLUMN_WIDTH * _SUMMARY_WIDTH
    widths = [w * box_width for w in _SUMMARY_COLS]
    aligns = ["left", "center"]
    instant_sold = daily_report.get("InstantTicketSold") or 0
    online_sold = daily_report.get("OnlineTicketSold") or 0
    cashed = (daily_report.get("InstantTicketCashed") or 0) + (
        daily_report.get("OnlineTicketCashed") or 0
    )
    due = daily_report.get("TotalDue")
    if due is None:
        due = instant_sold + online_sold - cashed
    rows = [
        ("Instant Lotto", instant_sold),
        ("Online Lotto (S.R. 50)", online_sold),
        ("Total", instant_sold + online_sold),
        ("S.R. 34", cashed),
    ]
    for label, value in rows:
        y = _draw_row(c, x, y, row_height, widths, [label, _format_money(value)], aligns)
    return _draw_row(
        c, x, y, row_height, widths, ["Due", _format_money(due)], aligns,
        bold=[False, True],
    )
