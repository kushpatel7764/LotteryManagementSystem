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
    new_df = df.drop(columns=["Top Prize", "Prizes Remaining", "Odds of Winning"])
    return new_df

def insert_new_ticket_name_to_lookup_table(db_path, file_name="TicketNameLook_GM_Track.txt"):
    create_empty_gm_track_file(file_name) # in case ticketNamelook_gm_track is not there
    # make sure the database with the lookup table is present before doing anything
    if len(compare_game_numbers(db_path, file_name)["in_file_not_in_db"]) > 0:
        remove_TicketName_GM_Track(file_name)
        create_empty_gm_track_file(file_name) # put it back after removing data
    lottery_lookup_table = get_lottery_net_lookup_table()
    for _, row in lottery_lookup_table.iterrows():
        # make sure gm is not in the lookup table before inserting a new name
        if not is_gm_in_lookup_table(row["Game No."], file_name):
            Database.insert_Ticket_name(db_path, row["Game Name"], row["Game No."])
            track_gms_in_lookup_table(db_path)
        
def remove_TicketName_GM_Track(file_name):
    parent_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
    parent_dir = os.path.dirname(parent_dir)  # Go one level up
    db_path = os.path.join(parent_dir, file_name)
    os.remove(db_path)
        
def track_gms_in_lookup_table(db_path, file_name="TicketNameLook_GM_Track.txt"):
    """
    Get Game numbers from lookup table and store them in file for use
    """
    lookup_gm = DatabaseQueries.get_gm_from_lookup(db_path)
    with open(file_name, "w") as f:
        temp_string = ""
        for i,item in enumerate(lookup_gm):
            if i == len(lookup_gm) - 1:
                temp_string += item
            else:
                temp_string += item + "\n"
        f.write(temp_string)

def is_gm_in_lookup_table(g_num,file_name):
    game_number_list = load_from_gm_track_file(file_name)
    if g_num in game_number_list:
        return True
    else:
        return False

def load_from_gm_track_file(file_name):
    game_number_list = []
    with open(file_name, "r") as f:
        for line in f:
            game_number_list.append(line.strip("\n"))
    return game_number_list
    
    
def is_lottery_DB_present(file_name="Lottery_Management_Database.db"):
    parent_dir = os.path.dirname(os.path.abspath(__file__))  # Current script directory
    parent_dir = os.path.dirname(parent_dir)  # Go one level up
    db_path = os.path.join(parent_dir, file_name)
    return os.path.exists(db_path)

def compare_game_numbers(db_path, track_file_path):
    # GET Gamenumber from Lookup table
    lookup_table_game_numbers = DatabaseQueries.get_gm_from_lookup(db_path)

    # Load game_number from the TicketNameLook_GM_Track file
    track_df = load_from_gm_track_file(track_file_path)
    file_game_numbers = set(track_df)

    # Compare
    # Will remove elements from file_game_number that are also in lookup_table_game_number
    in_file_not_in_db = file_game_numbers - lookup_table_game_numbers
    
    return {
        "in_file_not_in_db": in_file_not_in_db,
        "common": lookup_table_game_numbers & file_game_numbers
    }
    
def create_empty_gm_track_file(file_name):
    if not os.path.exists(file_name):
        with open(file_name, 'w') as f:
            pass  # Just create an empty file

