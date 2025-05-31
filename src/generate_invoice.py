from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime

def generate_lottery_invoice_pdf(filename, store_info, invoice_log, invoice_number, payment_method, tax=0.0):
    c = canvas.Canvas(filename, pagesize=LETTER)
    width, height = LETTER

    # Store Info
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "🎟️ LOTTERY TICKET SALE INVOICE")

    c.setFont("Helvetica", 10)
    y = height - 80
    for key, value in store_info.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 14

    # Invoice & Date
    now = datetime.now()
    c.drawString(400, height - 80, f"Invoice No.: {invoice_number}")
    c.drawString(400, height - 95, f"Date: {now.strftime('%m/%d/%Y')}")
    c.drawString(400, height - 110, f"Time: {now.strftime('%I:%M %p')}")

    # Table Headers
    y -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Ticket Name")
    c.drawString(180, y, "Game No.")
    c.drawString(275, y, "Book ID")
    c.drawString(345, y, "Price")
    c.drawString(400, y, "Open")
    c.drawString(450, y, "Close")
    c.drawString(500, y, "Sold")
    y -= 10
    c.line(50, y, 550, y)
    y -= 15

    # Table Rows
    c.setFont("Helvetica", 10)
    subtotal = 0.0
    for log in invoice_log:
        c.drawString(50, y, invoice_log["TicketName"])
        c.drawString(180, y, invoice_log["Ticket_GameNumber"])
        c.drawString(275, y, invoice_log("ActiveBookID"))
        c.drawString(345, y, f"${invoice_log["TicketPrice"]:.2f}")
        c.drawString(400, y, invoice_log["Open"])
        c.drawString(450, y, invoice_log["Close"])
        c.drawString(500, y, invoice_log["Sold"])
        y -= 18

    # Payment Summary
    tax_amount = subtotal * tax
    total = subtotal + tax_amount
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Instant Sold:")
    c.drawString(140, y, f"${subtotal:.2f}")
    y -= 15
    c.drawString(50, y, "Instant Cashed:")
    c.drawString(140, y, f"${tax_amount:.2f}")
    y -= 15
    c.drawString(50, y, "Online Sold:")
    c.drawString(140, y, f"${total:.2f}")
    y -= 15
    c.drawString(50, y, "Online Cashed:")
    c.drawString(140, y, payment_method)
    y -= 15
    c.drawString(50, y, "Cash On Hand:")
    c.drawString(140, y, payment_method)
    y -= 15
    c.drawString(50, y, "Total Due:")
    c.drawString(140, y, payment_method)

    # Footer
    y -= 40
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, y, "Note: All lottery ticket sales are final. No refunds or exchanges.")
    y -= 15
    c.drawString(50, y, "Thank you for your purchase and good luck! 🍀")

    c.save()
