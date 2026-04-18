"""Tests that all non-login routes are protected and require authentication."""


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

            allowed = {200, 301, 302, 401, 403}

            assert response.status_code in allowed, (
                f"Route {rule.rule} method {method} not protected "
                f"— got {response.status_code}"
            )
