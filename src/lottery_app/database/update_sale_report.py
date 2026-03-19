"""
Database management module for the Sales Report table in lottery database system.
"""

import datetime
import sqlite3

from lottery_app.database.setup_database import initialize_database
from lottery_app.decorators import get_db_cursor


def update_sale_report(  # pylint: disable=too-many-arguments
    database_path,
    instant_sold,
    online_sold,
    instant_cashed,
    online_cashed,
    *,  # everything after this must be passed by name
    cash_on_hand,
    report_id,
    date=datetime.datetime.now(datetime.timezone.utc).time().strftime("%H:%M:%S"),
):
    """
    Updates a finalized SaleReport entry with totals for ticket sales and cash.

    Parameters:
        database_path (str): Path to the SQLite database.
        instant_sold (int): Number of instant tickets sold.
        online_sold (int): Number of online tickets sold.
        instant_cashed (int): Number of instant tickets cashed.
        online_cashed (int): Number of online tickets cashed.
        cash_on_hand (float): Amount of cash on hand at the time of the report.
        report_id (str or int): The ReportID identifying the sale report.
        date (str, optional): Time of the report update. Defaults to current UTC time.

    Returns:
        tuple:
            - ("ERROR UPDATING SALE REPORT for REPORTID(<report_id>): <error>", "error") on failure.

    """
    initialize_database(database_path)
    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
                UPDATE SaleReport
                SET
                    InstantTicketSold = ?,
                    OnlineTicketSold = ?,
                    InstantTicketCashed = ?,
                    OnlineTicketCashed = ?,
                    CashOnHand = ?,
                    ReportTime = ?
                WHERE ReportID = ?
            """,
                (
                    instant_sold,
                    online_sold,
                    instant_cashed,
                    online_cashed,
                    cash_on_hand,
                    date,
                    report_id,
                ),
            )
    except sqlite3.Error as e:
        return f"ERROR UPDATING SALE REPORT for REPORTID({report_id}): {e}", "error"

    return "SUCCESSFULLY UPDATED SALE REPORT TABLE", "success"


def add_daily_totals(cursor, daily_totals):  # add_Sale_Report
    """
    Query to add a new daily total entry into the SaleReport table.
    """
    cursor.execute(
        """
        INSERT INTO SaleReport (
            ReportID,
            InstantTicketSold,
            OnlineTicketSold,
            InstantTicketCashed,
            OnlineTicketCashed,
            CashOnHand
        ) VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            daily_totals["ReportID"],
            daily_totals["instant_sold"],
            daily_totals["online_sold"],
            daily_totals["instant_cashed"],
            daily_totals["online_cashed"],
            daily_totals["cash_on_hand"],
        ),
    )


def insert_daily_totals(database_path, daily_totals):
    """
    Inserts a new daily total entry into the SaleReport table.

    Parameters:
        database_path (str): Path to the SQLite database.
        daily_totals (dict): Dictionary containing daily total values to be inserted.
                             Must include a 'ReportID' key.

    Returns:
        tuple:
            - ("ERROR ADDING A SALE REPORT FOR REPORTID(<ReportID>): <error>", "error")
            if an error occurs.
            - None if insertion is successful.

    Description:
        This function uses the provided `daily_totals` dictionary
        to add a new row to the SaleReport table using the helper function `add_daily_totals`.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            add_daily_totals(cursor, daily_totals)
    except sqlite3.Error as e:
        return (
            f"ERROR ADDING A SALE REPORT FOR REPORTID({daily_totals['ReportID']}): {e}",
            "error",
        )

    return "SUCCESSFULLY UPDATED SALE REPORT TABLE", "success"


def update_sale_report_instant_sold(database_path, instant_sold, report_id):
    """
    Updates the `InstantTicketSold` field for a specific sale report.

    Parameters:
        database_path (str): Path to the SQLite database.
        instant_sold (int): The updated number of instant tickets sold.
        report_id (str): The ReportID of the report to be updated.

    Returns:
        tuple:
            - ("ERROR UPDATING INSTANT SOLD VALUE FOR SALES REPORTID(<report_id>):
            <error>", "error") on SQLite error.

    Description:
        This function updates the `InstantTicketSold` field for the specified ReportID
        in the SaleReport table.
    """

    initialize_database(database_path)

    try:
        with get_db_cursor(database_path) as cursor:
            cursor.execute(
                """
            UPDATE SaleReport
            SET InstantTicketSold = ?
            WHERE ReportID = ?;
            """,
                (instant_sold, report_id),
            )
    except sqlite3.Error as e:
        return (
            f"Error updating instant sold value for sales reportid({report_id}) : ".upper()
            + f"{e}",
            "error",
        )

    return "SUCCESSFULLY UPDATED SALE REPORT TABLE", "success"
