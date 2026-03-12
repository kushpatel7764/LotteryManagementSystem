import pytest
from unittest.mock import patch, MagicMock

from lottery_app.database.user_model import User


# --------------------------
# Fixtures
# --------------------------

@pytest.fixture
def fake_user_row():
    return (1, "kush", "hashedpass", "admin")


# --------------------------
# get_by_username
# --------------------------

@patch("lottery_app.database.user_model.get_db_cursor")
def test_get_by_username_found(mock_cursor_ctx, fake_user_row):

    cursor = MagicMock()
    cursor.fetchone.return_value = fake_user_row
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    user = User.get_by_username("kush")

    assert user.username == "kush"
    assert user.role == "admin"


@patch("lottery_app.database.user_model.get_db_cursor")
def test_get_by_username_not_found(mock_cursor_ctx):

    cursor = MagicMock()
    cursor.fetchone.return_value = None
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    user = User.get_by_username("ghost")

    assert user is None


# --------------------------
# get_by_id
# --------------------------

@patch("lottery_app.database.user_model.get_db_cursor")
def test_get_by_id_found(mock_cursor_ctx, fake_user_row):

    cursor = MagicMock()
    cursor.fetchone.return_value = fake_user_row
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    user = User.get_by_id(1)

    assert user.id == 1


# --------------------------
# create
# --------------------------

@patch("lottery_app.database.user_model.generate_password_hash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_create_user(mock_cursor_ctx, mock_hash):

    mock_hash.return_value = "hashedpass"

    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    User.create("kush", "password")

    cursor.execute.assert_called_once()


# --------------------------
# delete
# --------------------------

@patch("lottery_app.database.user_model.flash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_delete_user_success(mock_cursor_ctx, mock_flash):

    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    User.delete("kush")

    mock_flash.assert_called_once()


@patch("lottery_app.database.user_model.flash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_delete_user_exception(mock_cursor_ctx, mock_flash):

    mock_cursor_ctx.side_effect = Exception("db error")

    User.delete("kush")

    mock_flash.assert_called_once()


# --------------------------
# update_password
# --------------------------

@patch("lottery_app.database.user_model.generate_password_hash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_update_password(mock_cursor_ctx, mock_hash):

    mock_hash.return_value = "hashedpass"

    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    User.update_password(1, "newpass")

    cursor.execute.assert_called_once()


# --------------------------
# verify_password
# --------------------------

@patch("lottery_app.database.user_model.check_password_hash")
def test_verify_password(mock_check):

    mock_check.return_value = True

    user = User(1, "kush", "hashedpass")

    assert user.verify_password("password") is True