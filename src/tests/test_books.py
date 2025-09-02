import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Add project root

import pytest
from flask import url_for
from unittest.mock import patch

# Assuming your Flask app is created in app.py
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

# 1. Test GET request (should just redirect without triggering the procedure)
def test_activate_book_get_redirects(client):
    response = client.get("/activate_book")
    assert response.status_code == 302  # Redirect
    # The redirect location should include books.books_managment route
    assert "books.books_managment" in response.location or "books_managment" in response.location

# 2. Test POST with valid scanned code
@patch("routes.books.activate_book_procedure")
def test_activate_book_post_valid(mock_activate_book_procedure, client):
    mock_activate_book_procedure.return_value = ("Book activated successfully", "success")

    response = client.post("/activate_book", data={"activate_book_code": "ABC123"})

    assert response.status_code == 302  # Should redirect
    assert mock_activate_book_procedure.called
    called_arg = mock_activate_book_procedure.call_args[0][0]
    assert called_arg == "ABC123"  # Ensure the scanned code is passed correctly

    # Verify the redirect includes the message and type
    assert "message=Book+activated+successfully" in response.location
    assert "message_type=success" in response.location

# 3. Test POST with no scanned code (empty form)
@patch("routes.books.activate_book_procedure")
def test_activate_book_post_empty_code(mock_activate_book_procedure, client):
    mock_activate_book_procedure.return_value = ("No code provided", "error")

    response = client.post("/activate_book", data={"activate_book_code": ""})

    assert response.status_code == 302
    assert mock_activate_book_procedure.called
    assert mock_activate_book_procedure.call_args[0][0] == ""  # Empty string should be passed

    assert "message=No+code+provided" in response.location
    assert "message_type=error" in response.location

# 4. Test POST where activate_book_procedure returns an error message
@patch("routes.books.activate_book_procedure")
def test_activate_book_post_procedure_failure(mock_activate_book_procedure, client):
    mock_activate_book_procedure.return_value = ("Failed to activate book", "error")

    response = client.post("/activate_book", data={"activate_book_code": "INVALID123"})

    assert response.status_code == 302
    assert mock_activate_book_procedure.called
    assert "message=Failed+to+activate+book" in response.location
    assert "message_type=error" in response.location

# 5. Test POST with missing form field (simulate malformed POST)
@patch("routes.books.activate_book_procedure")
def test_activate_book_post_missing_field(mock_activate_book_procedure, client):
    mock_activate_book_procedure.return_value = ("Missing code", "error")

    response = client.post("/activate_book", data={})  # No activate_book_code key

    assert response.status_code == 302
    assert mock_activate_book_procedure.called
    assert mock_activate_book_procedure.call_args[0][0] is None  # Should pass None

    assert "message=Missing+code" in response.location
    assert "message_type=error" in response.location
    

# 1. Test successful deactivation
@patch("routes.books.Database.deactivate_book")
@patch("routes.books.check_error")
def test_deactivate_book_success(mock_check_error, mock_deactivate_book, client):
    mock_deactivate_book.return_value = True  # Simulate DB success
    mock_check_error.side_effect = lambda result, msg: msg.update({"message": "", "message_type": ""})

    response = client.post("/deactivate_book", json={"bookID": "BOOK123"})

    assert response.status_code == 200
    data = response.get_json()
    assert "redirect_url" in data
    assert "message" not in data
    assert mock_deactivate_book.called
    assert mock_deactivate_book.call_args[0][1] == "BOOK123"  # Ensure bookID passed


# 2. Test database error returned by check_error
@patch("routes.books.Database.deactivate_book")
@patch("routes.books.check_error")
def test_deactivate_book_db_error(mock_check_error, mock_deactivate_book, client):
    mock_deactivate_book.return_value = False
    mock_check_error.side_effect = lambda result, msg: msg.update({"message": "DB error", "message_type": "error"})

    response = client.post("/deactivate_book", json={"bookID": "BOOK123"})

    assert response.status_code == 500
    data = response.get_json()
    assert data["message"] == "DB error"
    assert data["message_type"] == "error"
    assert "redirect_url" in data


# 3. Test missing bookID field in JSON
@patch("routes.books.Database.deactivate_book")
@patch("routes.books.check_error")
def test_deactivate_book_missing_book_id(mock_check_error, mock_deactivate_book, client):
    mock_deactivate_book.return_value = True
    mock_check_error.side_effect = lambda result, msg: msg.update({"message": "", "message_type": ""})
    response = client.post("/deactivate_book", json={})  # No bookID
    assert response.status_code == 500  # Should fail because book_id=None
    data = response.get_json()
    assert "Unexpected error" in data["message"]
    assert data["message_type"] == "error"


# 4. Test invalid JSON payload
@patch("routes.books.Database.deactivate_book")
@patch("routes.books.check_error")
def test_deactivate_book_invalid_json(mock_check_error, mock_deactivate_book, client):
    response = client.post("/deactivate_book", data="not json", content_type="application/json")
    assert response.status_code == 500
    data = response.get_json()
    assert "Unexpected error" in data["message"]
    assert data["message_type"] == "error"


# 5. Test unexpected exception in route
@patch("routes.books.Database.deactivate_book", side_effect=Exception("Database connection lost"))
@patch("routes.books.check_error")
def test_deactivate_book_unexpected_exception(mock_check_error, mock_deactivate_book, client):
    response = client.post("/deactivate_book", json={"bookID": "BOOK123"})
    assert response.status_code == 500
    data = response.get_json()
    assert "Unexpected error deactivating book" in data["message"]
    assert data["message_type"] == "error"