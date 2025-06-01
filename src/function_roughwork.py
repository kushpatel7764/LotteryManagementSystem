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

