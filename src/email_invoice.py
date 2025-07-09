import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
import config_utils

def email_invoice(filename):
    # CONFIGURATION
    EMAIL_SENDER = 'kushpatelrp1234@gmail.com'
    EMAIL_PASSWORD = 'kuon pyps cxqk agft'  # Use App Password if 2FA is enabled
    EMAIL_RECEIVER = config_utils.load_config()["business_email"]
    FOLDER_PATH = config_utils.load_config()["invoice_output_path"]

    # Get today's date string (e.g., 07-08-2024)
    today_str = datetime.today().strftime('%m-%d-%Y')

    # Create email message
    msg = EmailMessage()
    msg['Subject'] = f"PDF Files for {today_str}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg.set_content(f"Attached is the Lottery Report PDF from {today_str}.")

    # Find and attach matching PDFs
    filepath = os.path.join(FOLDER_PATH, filename)
    with open(filepath, 'rb') as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=filename)

    # Send the email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

    print("Email sent successfully.")
