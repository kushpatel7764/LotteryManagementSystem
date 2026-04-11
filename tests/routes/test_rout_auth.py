"""Tests that all non-login routes are protected and require authentication."""
import pytest
from lottery_app.app import app as flask_app


@pytest.fixture
def client():
    """Return a test client using the actual Flask app."""
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.test_client() as test_client:
        yield test_client


def test_all_protected_routes_blocked_without_login(app, client):  # pylint: disable=redefined-outer-name
    """
    Ensures all routes EXCEPT /login do not allow access
    when the user is not logged in.
    """
    print("\n\nStarting route protection tests...\n\n")

    unprotected = {"/login", "/static"}

    routes = []
    for rule in app.url_map.iter_rules():
        if any(rule.rule.startswith(p) for p in unprotected):
            continue
        if "<" in rule.rule:
            continue
        routes.append(rule)

    assert routes, "No routes found — test setup issue."

    for rule in routes:
        for method in rule.methods:
            if method in ("HEAD", "OPTIONS"):
                continue

            if method == "GET":
                response = client.get(rule.rule)
            elif method == "POST":
                response = client.post(rule.rule)
            else:
                continue

            print(f"Checked protection for: {method} {rule.rule}")

            allowed = {301, 302, 401, 403}

            assert response.status_code in allowed, (
                f"Route {rule.rule} method {method} not protected "
                f"— got {response.status_code}"
            )
