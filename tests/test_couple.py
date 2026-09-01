from tests.conftest import join_couple, register_couple


def test_join_couple_success(couple):
    resp = couple["sarah"].get("/api/couple")
    data = resp.get_json()
    assert data["is_complete"] is True
    assert len(data["members"]) == 2
    names = {m["name"] for m in data["members"]}
    assert names == {"Tom", "Sarah"}


def test_invite_code_hidden_once_couple_is_full(couple):
    resp = couple["tom"].get("/api/couple")
    assert resp.get_json()["invite_code"] is None


def test_third_member_rejected(app, couple):
    from app.models import Couple

    with app.app_context():
        c = Couple.query.first()
        invite_code = c.invite_code

    third_client = app.test_client()
    resp = join_couple(third_client, invite_code, name="Alex", username="alex")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "couple_full"


def test_invalid_invite_code_rejected(app):
    client = app.test_client()
    resp = join_couple(client, "ZZZZZZ", name="Alex", username="alex")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "invalid_code"


def test_update_couple_settings(couple):
    resp = couple["tom"].patch("/api/couple", json={"name": "Tom & Sarah", "timezone": "Pacific/Auckland"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Tom & Sarah"
    assert data["timezone"] == "Pacific/Auckland"


def test_update_couple_rejects_bad_timezone(couple):
    resp = couple["tom"].patch("/api/couple", json={"timezone": "Not/ARealZone"})
    assert resp.status_code == 400


def test_delete_couple_requires_confirmation_phrase(couple):
    resp = couple["tom"].post("/api/couple/delete", json={"confirmation": "nope"})
    assert resp.status_code == 400

    resp = couple["tom"].post("/api/couple/delete", json={"confirmation": "DELETE"})
    assert resp.status_code == 200

    resp = couple["sarah"].get("/api/couple")
    assert resp.status_code in (401, 404, 500)
