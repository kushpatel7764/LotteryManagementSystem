import pytest
import pandas
import requests
from unittest.mock import patch, MagicMock

import lottery_app.game_number_lookup_table as lookup

#------------------------------------------------------------------------------
# Pytest: test suite for books management functions in lottery_app.game_number_lookup_table
#------------------------------------------------------------------------------

@pytest.fixture
def temp_db_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(lookup, "db_dir", tmp_path)
    return tmp_path

def test_get_lottery_net_lookup_table_success(monkeypatch):
    html = """
    <table class="bordered scratchOffs table-sort">
        <tr>
            <th>Game No.</th>
            <th>Game Name</th>
            <th>Top Prize</th>
            <th>Prizes Remaining</th>
            <th>Odds of Winning</th>
        </tr>
        <tr>
            <td>123</td>
            <td>Lucky Test</td>
            <td>$1,000</td>
            <td>10</td>
            <td>1 in 4</td>
        </tr>
    </table>
    """

    mock_response = MagicMock()
    mock_response.content = html.encode()

    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_response)

    df = lookup.get_lottery_net_lookup_table()

    assert isinstance(df, pandas.DataFrame)
    assert list(df.columns) == ["Game No.", "Game Name"]
    assert df.iloc[0]["Game No."] == "123"
    assert df.iloc[0]["Game Name"] == "Lucky Test"
    
def test_load_from_gm_track_file(temp_db_dir):
    file_name = "track.txt"
    path = temp_db_dir / file_name
    path.write_text("100\n200\n300\n")

    result = lookup.load_from_gm_track_file(file_name)

    assert result == ["100", "200", "300"]


def test_is_gm_in_lookup_table_true(temp_db_dir):
    file_name = "track.txt"
    (temp_db_dir / file_name).write_text("111\n222\n")

    assert lookup.is_gm_in_lookup_table("111", file_name) is True


def test_is_gm_in_lookup_table_false(temp_db_dir):
    file_name = "track.txt"
    (temp_db_dir / file_name).write_text("111\n222\n")

    assert lookup.is_gm_in_lookup_table("999", file_name) is False


def test_remove_ticketname_gm_track(temp_db_dir):
    file_name = "track.txt"
    path = temp_db_dir / file_name
    path.write_text("test")

    lookup.remove_ticketname_gm_track(file_name)

    assert not path.exists()

@patch("lottery_app.database.database_queries.get_gm_from_lookup")
def test_track_gms_in_lookup_table(mock_get_gm, temp_db_dir):
    mock_get_gm.return_value = {"101", "202"}

    lookup.track_gms_in_lookup_table("fake.db")

    path = temp_db_dir / "TicketNameLook_GM_Track.txt"
    content = path.read_text().splitlines()

    assert set(content) == {"101", "202"}


@patch("lottery_app.database.database_queries.get_gm_from_lookup")
def test_compare_game_numbers(mock_get_gm, temp_db_dir):
    mock_get_gm.return_value = {"100", "200"}

    file_name = "track.txt"
    (temp_db_dir / file_name).write_text("200\n300\n")

    result = lookup.compare_game_numbers("fake.db", file_name)

    assert result["in_file_not_in_db"] == {"300"}
    assert result["common"] == {"200"}


def test_is_lottery_db_present_true(temp_db_dir):
    db_name = "Lottery_Management_Database.db"
    (temp_db_dir / db_name).touch()

    assert lookup.is_lottery_db_present(db_name) is True


def test_is_lottery_db_present_false(temp_db_dir):
    assert lookup.is_lottery_db_present("missing.db") is False


@patch("lottery_app.game_number_lookup_table.track_gms_in_lookup_table")
@patch("lottery_app.game_number_lookup_table.update_ticket_name_lookup.insert_ticket_name")
@patch("lottery_app.game_number_lookup_table.compare_game_numbers")
@patch("lottery_app.game_number_lookup_table.get_lottery_net_lookup_table")
def test_insert_new_ticket_name_success(
    mock_fetch,
    mock_compare,
    mock_insert,
    mock_track,
    temp_db_dir,
):
    mock_compare.return_value = {"in_file_not_in_db": set()}
    mock_fetch.return_value = pandas.DataFrame([
        {"Game No.": "101", "Game Name": "Test Game"}
    ])

    msg, status = lookup.insert_new_ticket_name_to_lookup_table("fake.db")

    assert status == "success"
    assert "UPDATED SUCCESSFULLY" in msg
    mock_insert.assert_called_once()
    mock_track.assert_called()

@patch("lottery_app.game_number_lookup_table.compare_game_numbers")
@patch("lottery_app.game_number_lookup_table.get_lottery_net_lookup_table")
def test_insert_new_ticket_name_fetch_error(
    mock_fetch,
    mock_compare,
    temp_db_dir,
):
    mock_compare.return_value = {"in_file_not_in_db": set()}
    mock_fetch.side_effect = requests.RequestException("boom")

    msg, status = lookup.insert_new_ticket_name_to_lookup_table("fake.db")

    assert status == "error"
    assert "Error fetching data" in msg

