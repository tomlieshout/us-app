"""
Tests for the "accepted or skipped never shows again until the category
is replayed" behaviour (app/models/challenge.py, app/services/challenges.py).
"""

from app.extensions import db
from app.models import ActivityContent


def _create_content(app, category, prompt):
    with app.app_context():
        content = ActivityContent(activity_type="challenge", category=category, prompt=prompt)
        content.payload = {"requires_both": False}
        db.session.add(content)
        db.session.commit()
        return content.id


def test_accepting_removes_it_from_future_random_picks(app, couple):
    tom = couple["tom"]
    only_id = _create_content(app, "cute", "The only cute challenge")

    tom.post("/api/challenges/accept", json={"content_id": only_id})

    resp = tom.get("/api/challenges/random?category=cute")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "exhausted"


def test_skipping_removes_it_from_future_random_picks_too(app, couple):
    """The actual behaviour requested: a skip must count the same as an
    accept for "don't show me this again" purposes."""
    tom = couple["tom"]
    only_id = _create_content(app, "cute", "The only cute challenge")

    tom.post("/api/challenges/skip", json={"content_id": only_id})

    resp = tom.get("/api/challenges/random?category=cute")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "exhausted"


def test_category_exhausts_only_once_every_item_accepted_or_skipped(app, couple):
    a_id = _create_content(app, "funny", "Funny one")
    b_id = _create_content(app, "funny", "Funny two")
    tom = couple["tom"]

    tom.post("/api/challenges/accept", json={"content_id": a_id})
    # One still untouched - not exhausted yet, and /random must still
    # find the remaining one specifically.
    status = tom.get("/api/challenges/status?category=funny").get_json()
    assert status["exhausted"] is False
    resp = tom.get("/api/challenges/random?category=funny")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == b_id

    tom.post("/api/challenges/skip", json={"content_id": b_id})
    status = tom.get("/api/challenges/status?category=funny").get_json()
    assert status["exhausted"] is True
    resp = tom.get("/api/challenges/random?category=funny")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "exhausted"


def test_skip_is_idempotent(app, couple):
    tom = couple["tom"]
    content_id = _create_content(app, "deep", "Deep one")

    first = tom.post("/api/challenges/skip", json={"content_id": content_id}).get_json()
    second = tom.post("/api/challenges/skip", json={"content_id": content_id}).get_json()
    assert first["id"] == second["id"]


def test_skipped_challenge_cannot_be_completed(app, couple):
    tom = couple["tom"]
    content_id = _create_content(app, "deep", "Deep one")
    skipped = tom.post("/api/challenges/skip", json={"content_id": content_id}).get_json()

    resp = tom.post(f"/api/challenges/{skipped['id']}/complete")
    assert resp.status_code == 400


def test_replay_makes_engaged_challenges_available_again(app, couple):
    tom = couple["tom"]
    content_id = _create_content(app, "romantic", "The only romantic one")
    tom.post("/api/challenges/accept", json={"content_id": content_id})

    assert tom.get("/api/challenges/random?category=romantic").status_code == 404

    replay_resp = tom.post("/api/challenges/replay", json={"category": "romantic"})
    assert replay_resp.status_code == 200
    assert replay_resp.get_json()["cycle"] == 2

    resp = tom.get("/api/challenges/random?category=romantic")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == content_id

    # And it can be accepted again - a fresh row in the new cycle,
    # distinct from the cycle-1 history.
    accept_resp = tom.post("/api/challenges/accept", json={"content_id": content_id})
    assert accept_resp.status_code == 201
    assert accept_resp.get_json()["cycle"] == 2


def test_replay_keeps_old_cycle_as_permanent_history(app, couple):
    tom = couple["tom"]
    content_id = _create_content(app, "romantic", "The only romantic one")
    first = tom.post("/api/challenges/accept", json={"content_id": content_id}).get_json()

    tom.post("/api/challenges/replay", json={"category": "romantic"})
    second = tom.post("/api/challenges/accept", json={"content_id": content_id}).get_json()

    # /mine is a full history across every cycle, not just the current one.
    mine = tom.get("/api/challenges/mine?category=romantic").get_json()["challenges"]
    ids = {c["id"] for c in mine}
    assert first["id"] in ids
    assert second["id"] in ids
    assert first["id"] != second["id"]


def test_replaying_one_category_does_not_affect_another(app, couple):
    tom = couple["tom"]
    cute_id = _create_content(app, "cute", "The only cute one")
    funny_id = _create_content(app, "funny", "The only funny one")
    tom.post("/api/challenges/accept", json={"content_id": cute_id})
    tom.post("/api/challenges/accept", json={"content_id": funny_id})

    tom.post("/api/challenges/replay", json={"category": "cute"})

    assert tom.get("/api/challenges/random?category=cute").status_code == 200
    assert tom.get("/api/challenges/random?category=funny").status_code == 404
