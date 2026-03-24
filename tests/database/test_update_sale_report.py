from lottery_app.database.update_sale_report import (
    insert_daily_totals,
    update_sale_report,
    update_sale_report_instant_sold,
)
from lottery_app.decorators import get_db_cursor


def test_insert_daily_totals(temp_db):
    daily_totals = {
        "ReportID": "R1",
        "instant_sold": 10,
        "online_sold": 5,
        "instant_cashed": 2,
        "online_cashed": 1,
        "cash_on_hand": 200.0,
    }

    msg, status = insert_daily_totals(temp_db, daily_totals)
    assert status == "success"

    with get_db_cursor(temp_db) as cursor:
        cursor.execute("SELECT * FROM SaleReport WHERE ReportID='R1';")
        assert cursor.fetchone() is not None


def test_update_sale_report(temp_db):
    insert_daily_totals(
        temp_db,
        {
            "ReportID": "R2",
            "instant_sold": 0,
            "online_sold": 0,
            "instant_cashed": 0,
            "online_cashed": 0,
            "cash_on_hand": 0,
        },
    )

    msg, status = update_sale_report(
        temp_db,
        instant_sold=10,
        online_sold=5,
        instant_cashed=3,
        online_cashed=1,
        cash_on_hand=500,
        report_id="R2",
    )

    assert status == "success"


def test_update_sale_report_instant_sold(temp_db):
    insert_daily_totals(
        temp_db,
        {
            "ReportID": "R3",
            "instant_sold": 1,
            "online_sold": 1,
            "instant_cashed": 0,
            "online_cashed": 0,
            "cash_on_hand": 50,
        },
    )

    msg, status = update_sale_report_instant_sold(temp_db, 99, "R3")
    assert status == "success"

    with get_db_cursor(temp_db) as cursor:
        cursor.execute("SELECT InstantTicketSold FROM SaleReport WHERE ReportID='R3';")
        assert cursor.fetchone()[0] == 99
