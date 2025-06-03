import datetime
import generate_invoice
print("40401746360243005080000000076".__len__())
print("35600949981000515070000000091".__len__())
 
"TicketName, ActivationID"

# print(datetime.date.today().strftime("%d/%m/%Y"))

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
url = 'https://www.lottery.net/massachusetts/scratch-offs'
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")
table = soup.find("table", class_="bordered scratchOffs table-sort")
headers = soup.find_all("th")
rows = table.find_all("tr")
print(headers)
cells = []
for row in rows:
    cells.append(row.find_all("td"))


