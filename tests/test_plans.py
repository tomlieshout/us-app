import pytest

from tests.conftest import register_couple


def _create(client, **overrides):
    payload = {"title": "Test Plan", "category": "trips"}
    payload.update(overrides)
    return client.post("/api/plans", json=payload)


# ---------------------------------------------------------------- empty state

def test_empty_state(couple):
    tom = couple["tom"]

    cats = tom.get("/api/plans/categories").get_json()["categories"]
    assert len(cats) == 6
    assert {c["key"] for c in cats} == {
        "movies_shows", "dates", "holidays", "trips", "things_to_do", "wishlist",
    }
    assert all(c["count"] == 0 for c in cats)

    plans = tom.get("/api/plans").get_json()["plans"]
    assert plans == []


def test_statuses_endpoint(couple):
    tom = couple["tom"]
    statuses = tom.get("/api/plans/statuses").get_json()["statuses"]
    assert [s["key"] for s in statuses] == ["someday", "want_to_do", "planned", "done"]


# --------------------------------------------------------------------- create

def test_create_requires_title(couple):
    tom = couple["tom"]
    resp = _create(tom, title="   ")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "title_required"


def test_create_requires_valid_category(couple):
    tom = couple["tom"]
    resp = _create(tom, category="not_a_real_category")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_category"


def test_create_requires_valid_status(couple):
    tom = couple["tom"]
    resp = _create(tom, status="not_a_real_status")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_status"


def test_create_defaults_status_to_someday_and_not_private(couple):
    tom = couple["tom"]
    resp = _create(tom, title="Japan", category="trips")
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "someday"
    assert data["is_private"] is False
    assert data["added_by_name"] == "Tom"
    assert data["title"] == "Japan"


# ----------------------------------------------------------------------- list

def test_create_and_list_roundtrip(couple):
    tom = couple["tom"]
    _create(tom, title="Dune 3", category="movies_shows")
    _create(tom, title="Japan", category="trips")

    plans = tom.get("/api/plans").get_json()["plans"]
    assert len(plans) == 2
    assert {p["title"] for p in plans} == {"Dune 3", "Japan"}


def test_category_and_status_filters(couple):
    tom = couple["tom"]
    _create(tom, title="Dune 3", category="movies_shows", status="planned")
    _create(tom, title="Japan", category="trips", status="someday")
    _create(tom, title="Paris", category="trips", status="planned")

    trips = tom.get("/api/plans?category=trips").get_json()["plans"]
    assert {p["title"] for p in trips} == {"Japan", "Paris"}

    planned = tom.get("/api/plans?status=planned").get_json()["plans"]
    assert {p["title"] for p in planned} == {"Dune 3", "Paris"}

    trips_planned = tom.get("/api/plans?category=trips&status=planned").get_json()["plans"]
    assert {p["title"] for p in trips_planned} == {"Paris"}


def test_list_invalid_filters_rejected(couple):
    tom = couple["tom"]
    assert tom.get("/api/plans?category=nope").status_code == 400
    assert tom.get("/api/plans?status=nope").status_code == 400


def test_categories_endpoint_reflects_counts(couple):
    tom = couple["tom"]
    _create(tom, title="Dune 3", category="movies_shows")
    _create(tom, title="Japan", category="trips")
    _create(tom, title="Paris", category="trips")

    cats = {c["key"]: c["count"] for c in tom.get("/api/plans/categories").get_json()["categories"]}
    assert cats["movies_shows"] == 1
    assert cats["trips"] == 2
    assert cats["wishlist"] == 0


# ---------------------------------------------------------- shared item edits

def test_either_partner_can_edit_a_shared_plan(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    plan_id = _create(tom, title="Japan").get_json()["id"]

    resp = sarah.patch(f"/api/plans/{plan_id}", json={"notes": "Cherry blossom season?"})
    assert resp.status_code == 200
    assert resp.get_json()["notes"] == "Cherry blossom season?"


def test_either_partner_can_delete_a_shared_plan(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    plan_id = _create(tom, title="Japan").get_json()["id"]

    resp = sarah.delete(f"/api/plans/{plan_id}")
    assert resp.status_code == 200
    assert tom.get("/api/plans").get_json()["plans"] == []


def test_quick_complete_via_status_patch(couple):
    tom = couple["tom"]
    plan_id = _create(tom, title="Dinner reservation", category="dates").get_json()["id"]

    resp = tom.patch(f"/api/plans/{plan_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "done"


def test_edit_rejects_invalid_category_and_status(couple):
    tom = couple["tom"]
    plan_id = _create(tom, title="Japan").get_json()["id"]

    assert tom.patch(f"/api/plans/{plan_id}", json={"category": "nope"}).status_code == 400
    assert tom.patch(f"/api/plans/{plan_id}", json={"status": "nope"}).status_code == 400
    assert tom.patch(f"/api/plans/{plan_id}", json={"title": "  "}).status_code == 400


# --------------------------------------------------------------------- privacy

def test_private_plan_hidden_from_partner_content(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    plan_id = _create(tom, title="Surprise trip for Sarah's birthday", notes="Book flights by March", is_private=True).get_json()["id"]

    # Raw response inspection, not just "the UI doesn't show it" - per the
    # brief, privacy must hold at the API level.
    sarah_view = sarah.get(f"/api/plans/{plan_id}").get_json()
    assert "title" not in sarah_view
    assert "notes" not in sarah_view
    assert sarah_view["hidden"] is True
    assert sarah_view["is_private"] is True
    # existence + category + status + who added it are still visible, so
    # browsing a shared category doesn't silently drop rows
    assert sarah_view["category"] == "trips"
    assert sarah_view["added_by_name"] == "Tom"

    sarah_list = sarah.get("/api/plans").get_json()["plans"]
    assert len(sarah_list) == 1
    assert "title" not in sarah_list[0]


def test_private_plan_owner_sees_full_content(couple):
    tom = couple["tom"]
    plan_id = _create(tom, title="Surprise trip", notes="Book flights by March", is_private=True).get_json()["id"]

    tom_view = tom.get(f"/api/plans/{plan_id}").get_json()
    assert tom_view["title"] == "Surprise trip"
    assert tom_view["notes"] == "Book flights by March"
    assert "hidden" not in tom_view


def test_partner_cannot_mutate_private_plan(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    plan_id = _create(tom, title="Surprise trip", is_private=True).get_json()["id"]

    resp = sarah.patch(f"/api/plans/{plan_id}", json={"status": "done"})
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "not_allowed"

    resp = sarah.delete(f"/api/plans/{plan_id}")
    assert resp.status_code == 403

    # confirm the status genuinely didn't change server-side
    assert tom.get(f"/api/plans/{plan_id}").get_json()["status"] == "someday"


def test_owner_can_still_mutate_own_private_plan(couple):
    tom = couple["tom"]
    plan_id = _create(tom, title="Surprise trip", is_private=True).get_json()["id"]

    resp = tom.patch(f"/api/plans/{plan_id}", json={"status": "planned"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "planned"


def test_only_owner_can_change_privacy_flag(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    plan_id = _create(tom, title="Japan").get_json()["id"]  # shared, not private

    # Sarah didn't add it - she can edit other fields (shared item) but not flip privacy
    resp = sarah.patch(f"/api/plans/{plan_id}", json={"is_private": True})
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "not_allowed"
    assert tom.get(f"/api/plans/{plan_id}").get_json()["is_private"] is False

    # Tom, the owner, can
    resp = tom.patch(f"/api/plans/{plan_id}", json={"is_private": True})
    assert resp.status_code == 200
    assert resp.get_json()["is_private"] is True


# ------------------------------------------------------------- couple scoping

def test_cross_couple_access_denied(app, couple):
    tom = couple["tom"]
    plan_id = _create(tom, title="Japan").get_json()["id"]

    alex_client = app.test_client()
    register_couple(alex_client, name="Alex", username="alex")

    assert alex_client.get(f"/api/plans/{plan_id}").status_code == 404
    assert alex_client.patch(f"/api/plans/{plan_id}", json={"status": "done"}).status_code == 404
    assert alex_client.delete(f"/api/plans/{plan_id}").status_code == 404
    # and Alex's own (empty) list never includes Tom & Sarah's plan
    assert alex_client.get("/api/plans").get_json()["plans"] == []


def test_get_nonexistent_plan_404s(couple):
    tom = couple["tom"]
    assert tom.get("/api/plans/999999").status_code == 404
