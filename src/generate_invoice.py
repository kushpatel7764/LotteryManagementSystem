"""
Module for generating invoices.

This module provides functions to create invoices, populate them with client
and product data, and export them in desired formats (e.g., PDF or Excel).
"""

from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def generate_lottery_invoice_pdf(
    filename, store_info, invoice_log, invoice_number, daily_report
):
    """
    Generate a lottery ticket sale invoice as a PDF.

    Args:
        filename (str): Output PDF filename.
        store_info (dict): Store details to include in the header.
        invoice_log (list[dict]): List of ticket sales records.
        invoice_number (str): Unique invoice number.
        daily_report (dict): Daily financial summary including totals.

    Returns:
        None
    """
    c = canvas.Canvas(filename, pagesize=LETTER)
    _, height = LETTER

    y = _draw_store_info(c, store_info, height)

    _draw_invoice_header(c, invoice_number, height, datetime.now())

    y = _draw_ticket_table(c, y, invoice_log)

    y = _draw_daily_summary(c, y, daily_report)

    y = _draw_footer(c, y)

    c.save()


def _draw_store_info(c, store_info, height):
    # Store Info
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "🎟️ LOTTERY TICKET SALE INVOICE")

    c.setFont("Helvetica", 10)
    y = height - 80
    for key, value in store_info.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 14
    return y


def _draw_invoice_header(c, invoice_number, height, now):
    c.drawString(400, height - 80, f"Invoice No.: {invoice_number}")
    c.drawString(400, height - 95, f"Date: {now.strftime('%m/%d/%Y')}")
    c.drawString(400, height - 110, f"Time: {now.strftime('%I:%M %p')}")


def _draw_ticket_table(c, y, invoice_log):
    # Table Headers
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Ticket Name")
    c.drawString(225, y, "Game No.")
    c.drawString(295, y, "Book ID")
    c.drawString(365, y, "Price")
    c.drawString(420, y, "Open")
    c.drawString(470, y, "Close")
    c.drawString(520, y, "Sold")
    y -= 10
    c.line(50, y, 550, y)
    y -= 15

    # Table Rows
    c.setFont("Helvetica", 10)
    if invoice_log is not None:
        for log in invoice_log:
            c.drawString(50, y, log["TicketName"])
            c.drawString(225, y, log["Ticket_GameNumber"])
            c.drawString(295, y, log["ActiveBookID"])
            c.drawString(365, y, f"${log['TicketPrice']:.2f}")
            c.drawString(420, y, str(log["Open"]))
            c.drawString(470, y, str(log["Close"]))
            c.drawString(520, y, str(log["Sold"]))
            y -= 18
    else:
        print("Error: Invoice log is None")

    return y


def _draw_daily_summary(c, y, daily_report):
    # daily Summary
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Instant Sold:")
    c.drawString(140, y, f"${str(daily_report['InstantTicketSold'])}")
    y -= 15
    c.drawString(50, y, "Instant Cashed:")
    c.drawString(140, y, f"${str(daily_report['InstantTicketCashed'])}")
    y -= 15
    c.drawString(50, y, "Online Sold:")
    c.drawString(140, y, f"${str(daily_report['OnlineTicketSold'])}")
    y -= 15
    c.drawString(50, y, "Online Cashed:")
    c.drawString(140, y, f"${str(daily_report['OnlineTicketCashed'])}")
    y -= 15
    c.drawString(50, y, "Cash On Hand:")
    c.drawString(140, y, f"${str(daily_report['CashOnHand'])}")
    y -= 15
    c.drawString(50, y, "Total Due:")
    c.drawString(140, y, f"${str(daily_report['TotalDue'])}")
    return y


def _draw_footer(c, y):
    # Footer
    y -= 40
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        50,
        y,
        "Note: Thank you for your business! Please contact us for any questions or concerns.",
    )
    return y
