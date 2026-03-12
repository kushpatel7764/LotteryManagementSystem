import pytest
from unittest.mock import patch
import sqlite3


#------------------------------------------------------------------------------
# Pytest: test suite for books management functions in lottery_app.routes.books
#------------------------------------------------------------------------------

"""
This suite covers:
    ✔ GET + POST for /books_managment
    ✔ Flash message reconciliation
    ✔ Book listing & ticket lookup
    ✔ Activated book logic
    ✔ All error branches
    ✔ JSON routes
    ✔ Redirect-based messaging
    ✔ Database + runtime failures
"""

@pytest.fixture
def books_url():
    return "/books_managment"


@pytest.fixture
def activate_url():
    return "/activate_book"


@pytest.fixture
def deactivate_url():
    return "/deactivate_book"


@pytest.fixture
def delete_url():
    return "/delete_book"

def test_books_management_get(auth, client):
    auth.login()
    response = client.get("/books_managment")
    assert response.status_code == 200

def test_books_management_get_with_flash(auth, client):
    auth.login()
    response = client.get(
        "/books_managment?message=Hello&message_type=success",
        follow_redirects=True,
    )
    assert response.status_code == 200

# /books_managment — POST (add book)
@patch("lottery_app.routes.books.add_book_procedure")
def test_books_management_post_add_book_success(
    add_book_mock, auth, client
):
    auth.login()
    add_book_mock.return_value = ("Book added", "success")

    response = client.post(
        "/books_managment",
        data={"add_book_code": "12345"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    add_book_mock.assert_called_once_with("12345")

# Books table population & ticket name resolution
@patch("lottery_app.routes.books.database_queries.get_ticket_name")
@patch("lottery_app.routes.books.database_queries.get_books")
def test_books_management_books_with_ticket_names(
    get_books_mock,
    get_ticket_name_mock,
    auth,
    client,
):
    auth.login()

    get_books_mock.return_value = [
        {"BookID": 1, "GameNumber": "777"},
    ]
    get_ticket_name_mock.return_value = "Lucky 7"

    response = client.get("/books_managment")
    assert response.status_code == 200


# Activated books set
@patch("lottery_app.routes.books.database_queries.get_activated_books")
def test_books_management_activated_books(
    get_activated_books_mock,
    auth,
    client,
):
    auth.login()

    get_activated_books_mock.return_value = [
        {"ActiveBookID": 1},
        {"ActiveBookID": 2},
    ]

    response = client.get("/books_managment")
    assert response.status_code == 200

# /delete_book — invalid request
def test_delete_book_missing_id(auth, client):
    auth.login()
    response = client.post(
        "/delete_book",
        json={},
    )
    assert response.status_code == 400
    
# /delete_book — deactivate fails
@patch("lottery_app.routes.books.update_activated_books.deactivate_book")
def test_delete_book_deactivate_error(
    deactivate_mock, auth, client
):
    auth.login()
    deactivate_mock.side_effect = RuntimeError("Fail")

    response = client.post(
        "/delete_book",
        json={"bookID": 1},
    )

    assert response.status_code == 500
    
# /delete_book — success
@patch("lottery_app.routes.books.update_books.delete_book")
@patch("lottery_app.routes.books.update_activated_books.deactivate_book")
def test_delete_book_success(
    deactivate_mock,
    delete_mock,
    auth,
    client,
):
    auth.login()
    deactivate_mock.return_value = None
    delete_mock.return_value = None

    response = client.post(
        "/delete_book",
        json={"bookID": 1},
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["message_type"] == "success"
    
# /deactivate_book — invalid JSON
def test_deactivate_book_invalid(auth, client):
    auth.login()
    response = client.post("/deactivate_book", json={})
    assert response.status_code == 400
    
# /deactivate_book — DB error
@patch("lottery_app.routes.books.update_activated_books.deactivate_book")
def test_deactivate_book_db_error(
    deactivate_mock, auth, client
):
    auth.login()
    deactivate_mock.side_effect = sqlite3.Error("DB fail")

    response = client.post(
        "/deactivate_book",
        json={"bookID": 1},
    )

    assert response.status_code == 500
    
# /deactivate_book — success
@patch("lottery_app.routes.books.update_activated_books.deactivate_book")
def test_deactivate_book_success(
    deactivate_mock, auth, client
):
    auth.login()
    deactivate_mock.return_value = None

    response = client.post(
        "/deactivate_book",
        json={"bookID": 1},
    )

    assert response.status_code == 200

# /activate_book — invalid code
@patch("lottery_app.routes.books.activate_book_procedure")
def test_activate_book_invalid(
    activate_mock, auth, client
):
    auth.login()
    activate_mock.return_value = ("INVALID BARCODE", "error")

    response = client.post(
        "/activate_book",
        data={"activate_book_code": "BAD"},
    )

    assert response.status_code == 302
    
# /activate_book — success
@patch("lottery_app.routes.books.activate_book_procedure")
def test_activate_book_success(
    activate_mock, auth, client
):
    auth.login()
    activate_mock.return_value = ("Activated", "success")

    response = client.post(
        "/activate_book",
        data={"activate_book_code": "GOOD"},
    )

    assert response.status_code == 302

