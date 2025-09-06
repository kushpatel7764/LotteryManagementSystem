"""
Module for managing the Massachusetts lottery game number lookup table.

This module fetches the lottery scratch-off data, maintains a local tracking file,
and updates the database with new game numbers.
"""


import os

import pandas as pd
from pandas import DataFrame
import requests
from bs4 import BeautifulSoup

from src.database import database_queries, update_ticket_name_lookup


def get_lottery_net_lookup_table() -> DataFrame:
    """
    Fetches the Massachusetts scratch-off lottery table from lottery.net
    and returns a cleaned Pandas DataFrame excluding 'Top Prize', 'Prizes Remaining',
    and 'Odds of Winning' columns.
    """
    url = "https://www.lottery.net/massachusetts/scratch-offs"
    response = requests.get(url, timeout=10)
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
    new_df = df.drop(
        columns=[
            "Top Prize",
            "Prizes Remaining",
            "Odds of Winning"])
    return new_df


def insert_new_ticket_name_to_lookup_table(
    db_path, file_name="TicketNameLook_GM_Track.txt"
):
    """
    Inserts new lottery ticket names into the database lookup table.

    This function compares the tracking file with the database and inserts any
    new game numbers that are not already in the lookup table.

    Args:
        db_path (str): Path to the SQLite database.
        file_name (str): Path to the game number tracking file.

    Returns:
        tuple[str, str]: A message and status ('success' or 'error').
    """
    try:
        create_empty_gm_track_file(file_name)  # Ensure file exists
        # Check if we need to refresh the game number tracking file
        comparison = compare_game_numbers(db_path, file_name)
        if "in_file_not_in_db" not in comparison:
            return "Failed to compare game numbers.", "error"

        if len(comparison["in_file_not_in_db"]) > 0:
            remove_ticketname_gm_track(file_name)
            # put empty file back after removing data
            create_empty_gm_track_file(file_name)

        try:
            lottery_lookup_table = get_lottery_net_lookup_table()
        except (requests.RequestException, ValueError) as e:
            return f"Error fetching data from lottery.net: {str(e)}", "error"

        # Insert any new ticket names
        for _, row in lottery_lookup_table.iterrows():
            try:
                if not is_gm_in_lookup_table(row["Game No."], file_name):
                    update_ticket_name_lookup.insert_ticket_name(
                        db_path, row["Game Name"], row["Game No."]
                    )
                    track_gms_in_lookup_table(db_path)
            except (OSError, KeyError, TypeError) as e:
                return ( f"Failed inserting game number {row['Game No.']}: {str(e)}",
                    "error",
                )

        return "Game number lookup table updated successfully".upper(), "success"
    except (OSError, RuntimeError) as e:
        return f"Unexpected error in lookup table insertion: {str(e)}", "error"


def remove_ticketname_gm_track(file_name):
    """
    Deletes the game number tracking file.

    Args:
        file_name (str): The name of the tracking file to delete.

    Returns:
        None
    """
    parent_dir = os.path.dirname(os.path.abspath(
        __file__))  # Current script directory
    parent_dir = os.path.dirname(parent_dir)  # Go one level up
    db_path = os.path.join(parent_dir, file_name)
    os.remove(db_path)


def track_gms_in_lookup_table(db_path,
                              file_name="TicketNameLook_GM_Track.txt"):
    """
    Get Game numbers from lookup table and store them in file for use
    """
    lookup_gm = database_queries.get_gm_from_lookup(db_path)
    with open(file_name, "w", encoding="utf-8") as f:
        temp_string = ""
        for i, item in enumerate(lookup_gm):
            if i == len(lookup_gm) - 1:
                temp_string += item
            else:
                temp_string += item + "\n"
        f.write(temp_string)


def is_gm_in_lookup_table(g_num, file_name):
    """
    Checks if a given game number exists in the tracking file.

    Args:
        g_num (str): Game number to check.
        file_name (str): Path to the tracking file.

    Returns:
        bool: True if the game number exists, False otherwise.
    """
    game_number_list = load_from_gm_track_file(file_name)
    return g_num in game_number_list


def load_from_gm_track_file(file_name):
    """
    Loads all game numbers from the tracking file.

    Args:
        file_name (str): Path to the tracking file.

    Returns:
        list[str]: List of game numbers in the file.
    """
    game_number_list = []
    with open(file_name, "r",  encoding="utf-8") as f:
        for line in f:
            game_number_list.append(line.strip("\n"))
    return game_number_list


def is_lottery_db_present(file_name="Lottery_Management_Database.db"):
    """
    Checks whether the lottery database file exists.

    Args:
        file_name (str): Name of the database file.

    Returns:
        bool: True if the database exists, False otherwise.
    """
    parent_dir = os.path.dirname(os.path.abspath(
        __file__))  # Current script directory
    parent_dir = os.path.dirname(parent_dir)  # Go one level up
    db_path = os.path.join(parent_dir, file_name)
    return os.path.exists(db_path)


def compare_game_numbers(db_path, track_file_path):
    """
    Compares game numbers in the tracking file with the database lookup table.

    Args:
        db_path (str): Path to the SQLite database.
        track_file_path (str): Path to the game number tracking file.

    Returns:
        dict: Dictionary with:
            - 'in_file_not_in_db': Set of game numbers in file but not in DB.
            - 'common': Set of game numbers present in both.
    """
    # GET Gamenumber from Lookup table
    lookup_table_game_numbers = database_queries.get_gm_from_lookup(db_path)

    # Load game_number from the TicketNameLook_GM_Track file
    track_df = load_from_gm_track_file(track_file_path)
    file_game_numbers = set(track_df)

    # Compare
    # Will remove elements from file_game_number that are also in
    # lookup_table_game_number
    in_file_not_in_db = file_game_numbers - lookup_table_game_numbers

    return {
        "in_file_not_in_db": in_file_not_in_db,
        "common": lookup_table_game_numbers & file_game_numbers,
    }


def create_empty_gm_track_file(file_name):
    """
    Creates an empty game number tracking file if it does not exist.

    Args:
        file_name (str): Path to the tracking file.

    Returns:
        None
    """
    if not os.path.exists(file_name):
        with open(file_name, "w",  encoding="utf-8"):
            pass  # Just create an empty file
