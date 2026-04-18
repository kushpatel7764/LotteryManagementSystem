"""
Module for managing the lottery game number lookup table.

This module fetches scratch-off data from lottery.net (which covers 44 US
states), compares it against the local database, and inserts any new game
number / ticket name pairs into the TicketNameLookup table.

State names in URLs follow lottery.net slug conventions, e.g.:
    "massachusetts", "new-york", "california", "rhode-island"
"""

import os

import pandas as pd
from pandas import DataFrame
import requests
from bs4 import BeautifulSoup

from lottery_app.database import database_queries, update_ticket_name_lookup
from lottery_app.utils.config import db_dir

_LOTTERY_NET_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LotteryApp/1.0)"}
_REQUIRED_COLUMNS = {"Game No.", "Game Name", "Price"}


def get_lottery_net_lookup_table(state: str = "massachusetts") -> DataFrame:
    """
    Fetches the scratch-off lottery table from lottery.net for any US state
    and returns a DataFrame with 'Game No.' and 'Game Name' columns.

    lottery.net covers 44 US states. State names must match the URL slug used
    by the site, e.g. "new-york", "rhode-island", "california".

    Args:
        state: Lowercase URL slug for the state (default: "massachusetts").

    Returns:
        DataFrame with columns ['Game No.', 'Game Name'].

    Raises:
        requests.RequestException: On network or HTTP errors.
        ValueError: If no scratch-off table with the expected columns is found.
    """
    url = f"https://www.lottery.net/{state}/scratch-offs"
    response = requests.get(url, timeout=10, headers=_LOTTERY_NET_HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    # Locate the table by inspecting column headers rather than relying on a
    # CSS class name that could change with a site redesign.
    table = None
    for candidate in soup.find_all("table"):
        headers = {th.get_text(strip=True) for th in candidate.find_all("th")}
        if _REQUIRED_COLUMNS.issubset(headers):
            table = candidate
            break

    if table is None:
        raise ValueError(
            f"Could not find a scratch-off table with columns {_REQUIRED_COLUMNS} "
            f"on lottery.net for state: '{state}'"
        )

    all_headers = [th.get_text(strip=True) for th in table.find_all("th")]
    rows = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        parsed_row = [
            BeautifulSoup(str(cell), "html.parser").text.strip() for cell in cells
        ]
        rows.append(parsed_row)

    df = pd.DataFrame(rows, columns=all_headers)
    return df[["Game No.", "Game Name", "Price"]]


def insert_new_ticket_name_to_lookup_table(
    db_path, state: str = "massachusetts"
):
    """
    Fetches scratch-off data from lottery.net and inserts any game numbers not
    already present in the TicketNameLookup table.

    Game numbers already in the database are never re-fetched or re-inserted —
    the database is the source of truth for which names have already been
    recorded.

    Args:
        db_path (str): Path to the SQLite database.
        state (str): lottery.net state slug (default: "massachusetts").
                     Examples: "new-york", "california", "rhode-island".

    Returns:
        tuple[str, str]: A message and status ('success' or 'error').
    """
    try:
        try:
            lottery_lookup_table = get_lottery_net_lookup_table(state)
        except (requests.RequestException, ValueError) as e:
            return f"Error fetching data from lottery.net: {str(e)}", "error"

        existing = database_queries.get_gm_from_lookup(db_path)
        if isinstance(existing, tuple):
            # get_gm_from_lookup returns an error tuple on DB failure
            return f"Error reading existing game numbers: {existing[0]}", "error"

        for _, row in lottery_lookup_table.iterrows():
            try:
                if row["Game No."] not in existing:
                    update_ticket_name_lookup.insert_ticket_name(
                        db_path, row["Game Name"], row["Game No."]
                    )
                    existing.add(row["Game No."])
            except (OSError, KeyError, TypeError) as e:
                return (
                    f"Failed inserting game number {row['Game No.']}: {str(e)}",
                    "error",
                )

        return "GAME NUMBER LOOKUP TABLE UPDATED SUCCESSFULLY", "success"
    except (OSError, RuntimeError) as e:
        return f"Unexpected error in lookup table insertion: {str(e)}", "error"


def is_lottery_db_present(file_name="Lottery_Management_Database.db"):
    """
    Checks whether the lottery database file exists.

    Args:
        file_name (str): Name of the database file.

    Returns:
        bool: True if the database exists, False otherwise.
    """
    db_path = os.path.join(db_dir, file_name)
    return os.path.exists(db_path)
