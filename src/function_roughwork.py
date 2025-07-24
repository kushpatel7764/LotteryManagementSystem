import datetime
import generate_invoice
print("40401746360243005080000000076".__len__())
print("35600949981000515070000000091".__len__())
 
"TicketName, ActivationID"

# print(datetime.date.today().strftime("%d/%m/%Y"))
print(datetime.datetime.now(datetime.timezone.utc).time().strftime("%H:%M:%S"))

from bs4 import BeautifulSoup
import pandas as pd
import requests


def get_lottery_net_lookup_table():
    url = 'https://www.lottery.net/massachusetts/scratch-offs'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="bordered scratchOffs table-sort")
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    rows = table.find_all("tr")
    table_created = []

    
    for row in rows:
        table_created.append(row.find_all("td"))

    # Clean and parse each cell using BeautifulSoup
    rows = []
    for row in table_created:
        if not row:
            continue  # skip empty rows
        parsed_row = []
        for cell in row:
            soup = BeautifulSoup(str(cell), "html.parser")
            parsed_row.append(soup.text.strip())
        rows.append(parsed_row)
    
    df = pd.DataFrame(rows, columns=headers)
    new_df = df.drop(columns=[ "Top Prize", "Prizes Remaining", "Odds of Winning"])
    return new_df
    

df  = get_lottery_net_lookup_table()
# Get a sorted list of distinct prices
distinct_prices = df["Price"].unique()
print(distinct_prices)
