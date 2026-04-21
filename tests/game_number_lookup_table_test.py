"""Tests for the game_number_lookup_table module."""

from unittest.mock import MagicMock, patch

import pandas
import pytest
import requests

import lottery_app.game_number_lookup_table as lookup

# pylint: disable=redefined-outer-name

# ------------------------------------------------------------------------------
# Pytest: test suite for books management functions in lottery_app.game_number_lookup_table
# ------------------------------------------------------------------------------


@pytest.fixture
def temp_db_dir(tmp_path, monkeypatch):
    """Monkeypatch db_dir to a temporary directory and return it."""
    monkeypatch.setattr(lookup, "db_dir", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# get_lottery_net_lookup_table
# ---------------------------------------------------------------------------


def _make_html_response(game_no, game_name, state_class=""):
    """Build a minimal HTML page with a scratch-off table."""
    return f"""
    <html><body>
    <table{state_class}>
        <tr>
            <th>Game No.</th>
            <th>Game Name</th>
            <th>Price</th>
            <th>Prizes Remaining</th>
            <th>Odds of Winning</th>
        </tr>
        <tr>
            <td>{game_no}</td>
            <td>{game_name}</td>
            <td>$1</td>
            <td>10</td>
            <td>1 in 4</td>
        </tr>
    </table>
    </body></html>
    """


def test_get_lottery_net_lookup_table_default_state(monkeypatch):
    """get_lottery_net_lookup_table defaults to massachusetts."""
    captured = {}

    def fake_get(url, **_kwargs):
        captured["url"] = url
        mock_resp = MagicMock()
        mock_resp.content = _make_html_response("123", "Lucky Test").encode()
        return mock_resp

    monkeypatch.setattr(requests, "get", fake_get)
    lookup.get_lottery_net_lookup_table()
    assert "massachusetts" in captured["url"]


def test_get_lottery_net_lookup_table_custom_state(monkeypatch):
    """get_lottery_net_lookup_table uses the provided state slug in the URL."""
    captured = {}

    def fake_get(url, **_kwargs):
        captured["url"] = url
        mock_resp = MagicMock()
        mock_resp.content = _make_html_response("456", "NY Winner").encode()
        return mock_resp

    monkeypatch.setattr(requests, "get", fake_get)
    lookup.get_lottery_net_lookup_table("new-york")
    assert "new-york" in captured["url"]


def test_get_lottery_net_lookup_table_returns_correct_columns(monkeypatch):
    """DataFrame returned has exactly Game No. and Game Name columns."""
    mock_resp = MagicMock()
    mock_resp.content = _make_html_response("123", "Lucky Test").encode()
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    df = lookup.get_lottery_net_lookup_table()

    assert isinstance(df, pandas.DataFrame)
    assert list(df.columns) == ["Game No.", "Game Name", "Price"]
    assert df.iloc[0]["Game No."] == "123"
    assert df.iloc[0]["Game Name"] == "Lucky Test"


def test_get_lottery_net_lookup_table_raises_on_missing_table(monkeypatch):
    """ValueError raised when page has no table with the required headers."""
    mock_resp = MagicMock()
    mock_resp.content = b"<html><body><p>No table here</p></body></html>"
    monkeypatch.setattr(requests, "get", lambda *a, **k: mock_resp)

    with pytest.raises(ValueError, match="Could not find a scratch-off table"):
        lookup.get_lottery_net_lookup_table("unknown-state")


def test_get_lottery_net_lookup_table_raises_on_network_error(monkeypatch):
    """requests.RequestException propagates from get_lottery_net_lookup_table."""
    monkeypatch.setattr(
        requests, "get", MagicMock(side_effect=requests.RequestException("offline"))
    )
    with pytest.raises(requests.RequestException):
        lookup.get_lottery_net_lookup_table()


# ---------------------------------------------------------------------------
# insert_new_ticket_name_to_lookup_table
# ---------------------------------------------------------------------------


@patch("lottery_app.game_number_lookup_table.database_queries.get_gm_from_lookup")
@patch(
    "lottery_app.game_number_lookup_table.update_ticket_name_lookup.insert_ticket_name"
)
@patch("lottery_app.game_number_lookup_table.get_lottery_net_lookup_table")
def test_insert_new_ticket_name_success(mock_fetch, mock_insert, mock_get_gm, temp_db_dir):  # pylint: disable=unused-argument
    """New game numbers are inserted; already-known ones are skipped."""
    mock_fetch.return_value = pandas.DataFrame(
        [
            {"Game No.": "101", "Game Name": "Test Game"},
            {"Game No.": "202", "Game Name": "Already Known"},
        ]
    )
    mock_get_gm.return_value = {"202"}  # 202 already in DB

    msg, status = lookup.insert_new_ticket_name_to_lookup_table("fake.db")

    assert status == "success"
    assert "UPDATED SUCCESSFULLY" in msg
    # Only the new game number (101) should be inserted
    mock_insert.assert_called_once_with("fake.db", "Test Game", "101")


@patch("lottery_app.game_number_lookup_table.database_queries.get_gm_from_lookup")
@patch("lottery_app.game_number_lookup_table.get_lottery_net_lookup_table")
def test_insert_new_ticket_name_no_duplicates(mock_fetch, mock_get_gm, temp_db_dir):  # pylint: disable=unused-argument
    """Game numbers already in the database are never re-inserted."""
    mock_fetch.return_value = pandas.DataFrame(
        [{"Game No.": "101", "Game Name": "Already There"}]
    )
    mock_get_gm.return_value = {"101"}

    with patch(
        "lottery_app.game_number_lookup_table.update_ticket_name_lookup.insert_ticket_name"
    ) as mock_insert:
        _msg, status = lookup.insert_new_ticket_name_to_lookup_table("fake.db")

    assert status == "success"
    mock_insert.assert_not_called()


@patch("lottery_app.game_number_lookup_table.get_lottery_net_lookup_table")
def test_insert_new_ticket_name_fetch_error(mock_fetch, temp_db_dir):  # pylint: disable=unused-argument
    """A fetch error returns an error status and message."""
    mock_fetch.side_effect = requests.RequestException("boom")

    msg, status = lookup.insert_new_ticket_name_to_lookup_table("fake.db")

    assert status == "error"
    assert "Error fetching data" in msg


@patch("lottery_app.game_number_lookup_table.database_queries.get_gm_from_lookup")
@patch("lottery_app.game_number_lookup_table.get_lottery_net_lookup_table")
def test_insert_new_ticket_name_db_read_error(mock_fetch, mock_get_gm, temp_db_dir):  # pylint: disable=unused-argument
    """A DB error from get_gm_from_lookup returns an error status."""
    mock_fetch.return_value = pandas.DataFrame(
        [{"Game No.": "101", "Game Name": "Test Game"}]
    )
    mock_get_gm.return_value = ("DATABASE ERROR IN get_gm_from_lookup: ...", "error")

    msg, status = lookup.insert_new_ticket_name_to_lookup_table("fake.db")

    assert status == "error"
    assert "Error reading existing game numbers" in msg


@patch("lottery_app.game_number_lookup_table.get_lottery_net_lookup_table")
def test_insert_new_ticket_name_uses_state_parameter(mock_fetch, temp_db_dir):  # pylint: disable=unused-argument
    """The state parameter is forwarded to get_lottery_net_lookup_table."""
    mock_fetch.side_effect = requests.RequestException("offline")

    lookup.insert_new_ticket_name_to_lookup_table("fake.db", state="new-york")

    mock_fetch.assert_called_once_with("new-york")


# ---------------------------------------------------------------------------
# is_lottery_db_present
# ---------------------------------------------------------------------------


def test_is_lottery_db_present_true(temp_db_dir):
    """Returns True when the database file exists."""
    db_name = "Lottery_Management_Database.db"
    (temp_db_dir / db_name).touch()
    assert lookup.is_lottery_db_present(db_name) is True


def test_is_lottery_db_present_false(temp_db_dir):  # pylint: disable=unused-argument
    """Returns False when the database file is missing."""
    assert lookup.is_lottery_db_present("missing.db") is False
