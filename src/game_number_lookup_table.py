import requests
from bs4 import BeautifulSoup
import pandas as pd
import Database
import DatabaseQueries
import os


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

    # Create DataFrame
    df = pd.DataFrame(rows, columns=headers)
    new_df = df.drop(columns=['Price', "Top Prize", "Prizes Remaining", "Odds of Winning"])
    return new_df

def insert_new_ticket_name_to_lookup_table(db_path):
    # make sure the database with the lookup table is present before doing anything
    if is_lottery_DB_present():
        lottery_lookup_table = get_lottery_net_lookup_table()
        for _, row in lottery_lookup_table.iterrows():
            # make sure gm is not in the lookup table before inserting a new name
            if not is_gm_in_lookup_table(row["Game No."]):
                Database.insert_Ticket_name(db_path, row["Game Name"], row["Game No."])
                track_gms_in_lookup_table(db_path)
    else:
        file_name="TicketNameLook_GM_Track"
        parent_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
        parent_dir = os.path.dirname(parent_dir)  # Go one level up
        db_path = os.path.join(parent_dir, file_name)
        os.remove(db_path)
        
def track_gms_in_lookup_table(db_path, file_name="TicketNameLook_GM_Track"):
    """
    Get Game numbers from lookup table and store them in file for use
    """
    lookup_gm = DatabaseQueries.get_gm_from_lookup(db_path)
    with open(file_name, "w") as f:
        temp_string = ""
        for tuple in lookup_gm:
            temp_string += tuple[0] + "\n"
        f.write(temp_string)

def is_gm_in_lookup_table(g_num,file_name="TicketNameLook_GM_Track"):
    game_number_list = []
    with open(file_name, "r") as f:
        for line in f:
            game_number_list.append(line.strip("\n"))
    if g_num in game_number_list:
        return True
    else:
        return False
    
def is_lottery_DB_present(file_name="Lottery_Management_Database.db"):
    parent_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
    parent_dir = os.path.dirname(parent_dir)  # Go one level up
    db_path = os.path.join(parent_dir, file_name)
    return os.path.exists(db_path)