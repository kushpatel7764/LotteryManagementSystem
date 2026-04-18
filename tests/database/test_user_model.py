"""Tests for lottery_app.database.user_model.User."""

from unittest.mock import patch, MagicMock

import pytest

from lottery_app.database.user_model import User

# pylint: disable=redefined-outer-name

# --------------------------
# Fixtures
# --------------------------


@pytest.fixture
def fake_user_row():
    """Return a tuple representing a raw user row from the database."""
    return (1, "kush", "hashedpass", "admin")


# --------------------------
# get_by_username
# --------------------------


@patch("lottery_app.database.user_model.get_db_cursor")
def test_get_by_username_found(mock_cursor_ctx, fake_user_row):
    """Test that get_by_username returns a User object when the user exists."""
    cursor = MagicMock()
    cursor.fetchone.return_value = fake_user_row
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    user = User.get_by_username("kush")

    assert user.username == "kush"
    assert user.role == "admin"


@patch("lottery_app.database.user_model.get_db_cursor")
def test_get_by_username_not_found(mock_cursor_ctx):
    """Test that get_by_username returns None when the user does not exist."""
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
    """Test that get_by_id returns a User object with the correct ID."""
    cursor = MagicMock()
    cursor.fetchone.return_value = fake_user_row
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    user = User.get_by_id(1)

    assert user.id == 1


# --------------------------
# create
# --------------------------


@patch("lottery_app.database.user_model.flash")
@patch("lottery_app.database.user_model.generate_password_hash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_create_user(mock_cursor_ctx, mock_hash, mock_flash):  # pylint: disable=unused-argument
    """Test that User.create hashes the password and inserts a row."""
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
    """Test that User.delete calls flash once on success."""
    cursor = MagicMock()
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    User.delete("kush")

    mock_flash.assert_called_once()


@patch("lottery_app.database.user_model.flash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_delete_user_exception(mock_cursor_ctx, mock_flash):  # pylint: disable=unused-argument
    """Test that User.delete flashes an error when a sqlite3.Error occurs."""
    import sqlite3 as _sqlite3  # pylint: disable=import-outside-toplevel
    mock_cursor_ctx.side_effect = _sqlite3.OperationalError("db error")

    User.delete("kush")

    mock_flash.assert_called_once()


# --------------------------
# update_password
# --------------------------


@patch("lottery_app.database.user_model.generate_password_hash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_update_password(mock_cursor_ctx, mock_hash):
    """Test that User.update_password hashes the new password and updates the row."""
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
    """Test that User.verify_password returns True when the password matches."""
    mock_check.return_value = True

    user = User(1, "kush", "hashedpass")

    assert user.verify_password("password") is True


# ============================================================
# NEW SECURITY AND EDGE-CASE TESTS
# ============================================================


@patch("lottery_app.database.user_model.check_password_hash")
def test_verify_password_returns_false_on_mismatch(mock_check):  # NEW
    """verify_password returns False for an incorrect password."""
    mock_check.return_value = False
    user = User(1, "kush", "hashedpass")
    assert user.verify_password("wrong_password") is False


def test_verify_password_empty_string():  # NEW
    """
    verify_password with an empty string must not raise — it delegates to
    check_password_hash which handles it gracefully.
    """
    with patch("lottery_app.database.user_model.check_password_hash") as mock_check:
        mock_check.return_value = False
        user = User(1, "kush", "hashedpass")
        result = user.verify_password("")
    assert result is False


@patch("lottery_app.database.user_model.get_db_cursor")
def test_get_by_username_uses_parameterised_query(mock_cursor_ctx):  # NEW
    """
    get_by_username must use a parameterised SQL placeholder ('?') and
    never embed the username directly into the query string.
    This prevents SQL injection.
    """
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    injection = "' OR '1'='1"
    User.get_by_username(injection)

    args, _ = cursor.execute.call_args
    query, params = args[0], args[1]

    assert "?" in query, "Query must use a parameterised placeholder"
    assert injection not in query, "Injection payload must not be in the query string"
    assert injection in params, "Injection payload must be in the params tuple"


@patch("lottery_app.database.user_model.get_db_cursor")
def test_get_by_id_uses_parameterised_query(mock_cursor_ctx):  # NEW
    """get_by_id must use a parameterised placeholder to prevent SQL injection."""
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    User.get_by_id(99)

    args, _ = cursor.execute.call_args
    query, params = args[0], args[1]
    assert "?" in query
    assert 99 in params


@patch("lottery_app.database.user_model.flash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_delete_protected_admin(mock_cursor_ctx, mock_flash):  # NEW
    """
    Attempting to delete a user with role 'default_admin' must flash
    'Cannot delete protected user.' and NOT execute the DELETE statement.
    """
    cursor = MagicMock()
    cursor.fetchone.return_value = ("default_admin",)  # role query result
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    User.delete("admin")

    args, _ = mock_flash.call_args
    assert "protected" in args[0].lower(), (
        "Must flash a 'protected' message for default_admin users."
    )

    # The DELETE statement must not have been executed
    executed_sqls = [call.args[0] for call in cursor.execute.call_args_list]
    delete_calls = [s for s in executed_sqls if "DELETE" in s.upper()]
    assert not delete_calls, "DELETE must not be called for a default_admin user."


@patch("lottery_app.database.user_model.flash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_create_user_hashes_password(mock_cursor_ctx, mock_flash):  # NEW  # pylint: disable=unused-argument
    """User.create must hash the password — the raw plaintext must never be stored."""
    captured_params = []

    cursor = MagicMock()

    def capture_execute(_query, params=None):
        if params:
            captured_params.extend(params)

    cursor.execute.side_effect = capture_execute
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    raw_password = "supersecretpassword"
    User.create("securitytest", raw_password)

    # Raw password must not appear in any parameter sent to the DB
    assert raw_password not in captured_params, (
        "Raw password was stored instead of its hash — use generate_password_hash."
    )


@patch("lottery_app.database.user_model.get_db_cursor")
def test_update_password_hashes_new_password(mock_cursor_ctx):  # NEW
    """update_password must hash the new password before storing it."""
    captured_params = []

    cursor = MagicMock()

    def capture_execute(_query, params=None):
        if params:
            captured_params.extend(params)

    cursor.execute.side_effect = capture_execute
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    new_raw = "my_new_plaintext_password"
    User.update_password(1, new_raw)

    assert new_raw not in captured_params, (
        "Plaintext password was stored — update_password must hash before saving."
    )


def test_user_model_role_defaults_to_standard():  # NEW
    """User constructor defaults role to 'standard' when not specified."""
    user = User(5, "anon", "hash")
    assert user.role == "standard"


@patch("lottery_app.database.user_model.flash")
@patch("lottery_app.database.user_model.get_db_cursor")
def test_create_duplicate_username_flashes_integrity_error(
    mock_cursor_ctx, mock_flash
):  # NEW
    """
    Creating a user with an existing username raises IntegrityError.
    The route must flash an informative message without crashing.
    """
    import sqlite3  # pylint: disable=import-outside-toplevel

    cursor = MagicMock()
    cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
    mock_cursor_ctx.return_value.__enter__.return_value = cursor

    User.create("existing_user", "password")

    args, _ = mock_flash.call_args
    assert "unique" in args[0].lower() or "integrity" in args[0].lower(), (
        "IntegrityError must produce an informative flash, not a silent failure."
    )
