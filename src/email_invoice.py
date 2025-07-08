import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage

# CONFIGURATION
EMAIL_SENDER = 'your_email@gmail.com'
EMAIL_PASSWORD = 'your_app_password'  # Use App Password if 2FA is enabled
EMAIL_RECEIVER = 'worker_email@example.com'
FOLDER_PATH = 'myfolder'

# Get today's date string (e.g., 2025-07-08)
today_str = datetime.today().strftime('%Y-%m-%d')

# Create email message
msg = EmailMessage()
msg['Subject'] = f"PDF Files for {today_str}"
msg['From'] = EMAIL_SENDER
msg['To'] = EMAIL_RECEIVER
msg.set_content(f"Attached are all PDF files from {today_str}.")

# Find and attach matching PDFs
for filename in os.listdir(FOLDER_PATH):
    if filename.endswith('.pdf') and today_str in filename:
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
