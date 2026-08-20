from app.models import User


def test_register_creates_user(client, app):
    resp = client.post(
        "/auth/register",
        data={
            "name": "Jane Farmer",
            "email": "jane@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert User.query.filter_by(email="jane@example.com").first() is not None


def test_register_rejects_mismatched_passwords(client):
    resp = client.post(
        "/auth/register",
        data={
            "name": "Jane Farmer",
            "email": "jane2@example.com",
            "password": "password123",
            "confirm_password": "nope",
        },
    )
    assert b"do not match" in resp.data


def test_login_with_valid_credentials(client, registered_user):
    resp = client.post("/auth/login", data=registered_user, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data or resp.request.path == "/dashboard"


def test_login_with_invalid_password_fails(client, registered_user):
    resp = client.post(
        "/auth/login",
        data={"email": registered_user["email"], "password": "wrongpass"},
    )
    assert b"Invalid email or password" in resp.data


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=True)
    assert b"log in" in resp.data.lower() or resp.request.path == "/auth/login"


def test_logout(client, registered_user):
    client.post("/auth/login", data=registered_user, follow_redirects=True)
    resp = client.get("/auth/logout", follow_redirects=True)
    assert resp.status_code == 200
    # Dashboard should now redirect to login again
    resp2 = client.get("/dashboard", follow_redirects=True)
    assert resp2.request.path == "/auth/login"
