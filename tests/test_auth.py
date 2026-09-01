from tests.conftest import join_couple, register_couple


def test_register_couple_creates_couple_and_logs_in(client):
    resp = register_couple(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["couple"]["invite_code"]
    assert data["user"]["username"] == "tom"

    me = client.get("/api/auth/me")
    assert me.get_json()["authenticated"] is True


def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/auth/register-couple",
        json={"name": "Tom", "username": "tom", "password": "short"},
    )
    assert resp.status_code == 400


def test_duplicate_username_rejected(client, app):
    register_couple(client, username="tom")
    other_client = app.test_client()
    resp = register_couple(other_client, username="tom")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "username_taken"


def test_login_logout(client):
    register_couple(client, username="tom")
    client.post("/api/auth/logout")
    me = client.get("/api/auth/me")
    assert me.get_json()["authenticated"] is False

    resp = client.post("/api/auth/login", json={"username": "tom", "password": "password1234"})
    assert resp.status_code == 200
    me = client.get("/api/auth/me")
    assert me.get_json()["authenticated"] is True


def test_login_wrong_password_rejected(client):
    register_couple(client, username="tom")
    client.post("/api/auth/logout")
    resp = client.post("/api/auth/login", json={"username": "tom", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_unauthorized_access_returns_401(client):
    resp = client.get("/api/couple")
    assert resp.status_code == 401
    resp = client.get("/api/rounds/current")
    assert resp.status_code == 401
