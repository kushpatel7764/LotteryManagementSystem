"""
Module for sending invoice PDFs via email.

This module loads configuration settings, attaches the generated PDF invoice, and sends it
to the configured business email using Gmail's SMTP over SSL.
"""

import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from lottery_app.utils.config import load_config


def email_invoice(filename):
    """
    Sends a lottery report invoice PDF via email.

    Args:
        filename (str): Name of the PDF file to send.

    Returns:
        None
    """
    # CONFIGURATION
    email_sender = "kushpatelrp1234@gmail.com"
    email_password = "kuon pyps cxqk agft"  # Use App Password if 2FA is enabled
    email_receiver = load_config()["business_email"]
    folder_path = load_config()["invoice_output_path"]

    # Get today's date string (e.g., 07-08-2024)
    today_str = datetime.today().strftime("%m-%d-%Y")

    # Create email message
    msg = EmailMessage()
    msg["Subject"] = f"PDF Files for {today_str}"
    msg["From"] = email_sender
    msg["To"] = email_receiver
    msg.set_content(f"Attached is the Lottery Report PDF from {today_str}.")

    # Find and attach matching PDFs
    filepath = os.path.join(folder_path, filename)
    with open(filepath, "rb") as f:
        file_data = f.read()
        msg.add_attachment(
            file_data, maintype="application", subtype="pdf", filename=filename
        )

    # Send the email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.send_message(msg)

    print("Email sent successfully.")
