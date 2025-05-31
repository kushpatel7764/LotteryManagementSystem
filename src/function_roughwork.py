import datetime
import generate_invoice
print("40401746360243005080000000076".__len__())
print("35600949981000515070000000091".__len__())
 
"TicketName, ActivationID"

print(datetime.date.today().strftime("%d/%m/%Y"))

import requests
from bs4 import BeautifulSoup

ma_lottery_page = requests.get("https://www.masslottery.com/games/draw-and-instants")
soup = BeautifulSoup(ma_lottery_page.text, "html.parser")

generate_invoice.generate_lottery_invoice_pdf("invoice_lottery.pdf", store_info, ticket_list, invoice_number="INV-2025-0001", payment_method="Cash", tax=0.0)
