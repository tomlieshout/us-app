"""
Tests for GET /api/home (app/services/home.py). Home has no data model of
its own, so most of these tests build real content/activity/state through
the actual systems Home reads from - only ActivityContent (classic_question/
would_you_rather) is constructed directly, matching the existing convention
in tests/test_spicy.py and tests/test_stats.py, since content is seed-only
and there's no creation endpoint for it.
"""

from datetime import date, datetime, timedelta
from unittest.mock import patch

from app.extensions import db
from app.models import ActivityContent, CoupleChallenge

_LANES = ["question", "game", "appreciation", "challenge", "plan"]


def _date_for_lane(lane_name, start=date(2026, 1, 1)):
    idx = _LANES.index(lane_name)
    d = start
    while d.toordinal() % len(_LANES) != idx:
        d = date.fromordinal(d.toordinal() + 1)
    return d


def _create_content(app, activity_type, category, payload, **kwargs):
    with app.app_context():
        content = ActivityContent(activity_type=activity_type, category=category, prompt="Test content", **kwargs)
        content.payload = payload
        db.session.add(content)
        db.session.commit()
        return content.id


def _home_on(client, lane_name):
    with patch("app.services.home.couple_local_today", return_value=_date_for_lane(lane_name)):
        return client.get("/api/home")


# ------------------------------------------------------------------ general

def test_home_requires_login(client):
    resp = client.get("/api/home")
    assert resp.status_code == 401


def test_home_action_lane_with_no_content_seeded(couple):
    """Appreciation/challenge/plan lanes need no ActivityContent at all -
    should never 500 or 404 on a bare-fresh couple."""
    tom = couple["tom"]
    resp = _home_on(tom, "appreciation")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["today"]["kind"] == "action"
    assert data["today"]["lane"] == "appreciation"
    assert data["today"]["state"] == "todo"


# --------------------------------------------------------------- action lane

def test_home_action_lane_flips_to_done_today(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    resp = _home_on(tom, "plan")
    assert resp.get_json()["today"]["state"] == "todo"

    tom.post("/api/plans", json={"title": "Weekend trip", "category": "trips"})

    resp = _home_on(tom, "plan")
    assert resp.get_json()["today"]["state"] == "done_today"


def test_home_challenge_action_lane_ignores_spicy_completion(app, couple):
    """A Spicy challenge completed today must not flip the action lane to
    done - same exclusion as Stats, not just a visibility rule."""
    tom, sarah = couple["tom"], couple["sarah"]
    content_id = _create_content(app, "challenge", "spicy", {"requires_both": False})
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    accepted = tom.post("/api/challenges/accept", json={"content_id": content_id}).get_json()
    tom.post(f"/api/challenges/{accepted['id']}/complete")

    resp = _home_on(tom, "challenge")
    assert resp.get_json()["today"]["state"] == "todo"


# --------------------------------------------------------------- reveal lane

def test_home_question_lane_shape(app, couple):
    tom = couple["tom"]
    _create_content(
        app, "classic_question", "relationship",
        {"question_type": "free_text", "options": None, "predict_text": None},
    )

    resp = _home_on(tom, "question")
    assert resp.status_code == 200
    today = resp.get_json()["today"]
    assert today["kind"] == "reveal"
    assert today["lane"] == "question"
    assert today["activity_type"] == "classic_question"
    assert today["activity"]["my_submitted"] is False
    assert "partner_submission" not in today["activity"]


def test_home_reveal_lane_never_leaks_partner_answer_pre_reveal(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(
        app, "classic_question", "relationship",
        {"question_type": "free_text", "options": None, "predict_text": None},
    )

    activity_id = _home_on(tom, "question").get_json()["today"]["activity"]["activity_id"]
    sarah.post(f"/api/activities/{activity_id}/submit", json={"answer_text": "Sarah's secret answer"})

    today = _home_on(tom, "question").get_json()["today"]
    assert today["activity"]["my_submitted"] is False
    assert today["activity"]["revealed"] is False
    # Partner already answered - Tom must be told THAT, never the content,
    # and the raw response must not carry the key at all pre-reveal.
    assert today["activity"]["partner_submitted"] is True
    assert "partner_submission" not in today["activity"]


def test_home_reveal_lane_waiting_then_ready(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(
        app, "classic_question", "relationship",
        {"question_type": "free_text", "options": None, "predict_text": None},
    )

    activity_id = _home_on(tom, "question").get_json()["today"]["activity"]["activity_id"]
    tom.post(f"/api/activities/{activity_id}/submit", json={"answer_text": "Tom's answer"})

    waiting = _home_on(tom, "question").get_json()["today"]
    assert waiting["activity"]["my_submitted"] is True
    assert waiting["activity"]["revealed"] is False

    sarah.post(f"/api/activities/{activity_id}/submit", json={"answer_text": "Sarah's answer"})

    ready = _home_on(tom, "question").get_json()["today"]
    assert ready["activity"]["revealed"] is True
    assert ready["activity"]["partner_submission"]["payload"]["answer_text"] == "Sarah's answer"


def test_home_game_lane_shape(app, couple):
    tom = couple["tom"]
    _create_content(app, "would_you_rather", "normal", {"option_a": "A", "option_b": "B"})

    today = _home_on(tom, "game").get_json()["today"]
    assert today["kind"] == "reveal"
    assert today["lane"] == "game"
    assert today["activity_type"] in ("would_you_rather", "know_each_other", "who_would")


def test_home_game_lane_falls_back_across_game_types(app, couple):
    """If today's rotated-to game type has no content but a DIFFERENT
    game type does, Home should find and use that one rather than giving
    up after just the first type."""
    tom = couple["tom"]
    # Only who_would has content - whichever type today's rotation lands
    # on first, the fallback should still find this.
    _create_content(app, "who_would", "normal", {"prompt_suffix": "do this?"})

    today = _home_on(tom, "game").get_json()["today"]
    assert today["kind"] == "reveal"
    assert today["activity_type"] == "who_would"


def test_home_game_lane_falls_back_to_action_lane_when_no_content_available(app, couple):
    """Only Spicy would_you_rather content exists and the couple is
    locked - every game type comes back empty, so Today's Activity must
    fall back to a content-free action lane rather than ever returning
    null (which would crash the frontend)."""
    tom = couple["tom"]
    _create_content(app, "would_you_rather", "spicy", {"option_a": "A", "option_b": "B"})

    resp = _home_on(tom, "game")
    assert resp.status_code == 200
    today = resp.get_json()["today"]
    assert today is not None
    assert today["kind"] == "action"


# ---------------------------------------------------------- recent activity

def test_home_recent_activity_includes_plan_and_appreciation(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/plans", json={"title": "Weekend trip", "category": "trips"})
    tom.post("/api/appreciation/send", json={"message_text": "You're wonderful"})

    resp = tom.get("/api/home")
    types = [item["type"] for item in resp.get_json()["recent_activity"]]
    assert "plan_added" in types
    assert "appreciation_received" in types


def test_home_recent_activity_includes_memory(couple):
    tom = couple["tom"]
    tom.post("/api/memories", json={"title": "Our first trip"})

    resp = tom.get("/api/home")
    items = resp.get_json()["recent_activity"]
    assert any(i["type"] == "memory_created" and "Our first trip" in i["text"] for i in items)


def test_home_recent_activity_includes_completed_challenge(app, couple):
    tom = couple["tom"]
    content_id = _create_content(app, "challenge", "cute", {"requires_both": False})
    accepted = tom.post("/api/challenges/accept", json={"content_id": content_id}).get_json()
    tom.post(f"/api/challenges/{accepted['id']}/complete")

    resp = tom.get("/api/home")
    types = [item["type"] for item in resp.get_json()["recent_activity"]]
    assert "challenge_completed" in types


def test_home_recent_activity_never_shows_spicy(app, couple):
    """Every source (Activity, Challenge) must exclude Spicy from Recent
    Activity unconditionally - even once unlocked, per the explicit
    'never show sensitive spicy information' requirement."""
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    wyr_id = _create_content(app, "would_you_rather", "spicy", {"option_a": "A", "option_b": "B"})
    challenge_content_id = _create_content(app, "challenge", "spicy", {"requires_both": False})

    activity = tom.get("/api/activities/random?category=spicy&activity_type=would_you_rather").get_json()
    tom.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})
    sarah.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})

    accepted = tom.post("/api/challenges/accept", json={"content_id": challenge_content_id}).get_json()
    tom.post(f"/api/challenges/{accepted['id']}/complete")

    resp = tom.get("/api/home")
    items = resp.get_json()["recent_activity"]
    assert all(i["type"] != "game_completed" for i in items)
    assert all(i["type"] != "challenge_completed" for i in items)
    assert len(items) == 0


def test_home_recent_activity_respects_plan_privacy(couple):
    """A private plan's title must not leak into the feed - same rule as
    the Plans system itself."""
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/plans", json={"title": "Surprise for Sarah", "category": "trips", "is_private": True})

    resp = sarah.get("/api/home")
    items = resp.get_json()["recent_activity"]
    plan_items = [i for i in items if i["type"] == "plan_added"]
    assert len(plan_items) == 1
    assert "Surprise for Sarah" not in plan_items[0]["text"]


def test_home_recent_activity_ordered_most_recent_first(app, couple):
    tom = couple["tom"]
    tom.post("/api/memories", json={"title": "Older memory"})
    tom.post("/api/memories", json={"title": "Newer memory"})

    resp = tom.get("/api/home")
    items = resp.get_json()["recent_activity"]
    memory_items = [i for i in items if i["type"] == "memory_created"]
    assert "Newer memory" in memory_items[0]["text"]
    assert "Older memory" in memory_items[1]["text"]


# --------------------------------------------------------------- champion

def test_home_champion_matches_stats_competitive(app, couple):
    """Home's champion must be exactly the subset of Stats' competitive
    numbers it claims to reuse, not a separately-computed value that could
    drift out of sync."""
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(app, "would_you_rather", "normal", {"option_a": "A", "option_b": "B"})
    activity = tom.get("/api/activities/random?activity_type=would_you_rather").get_json()
    tom.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})
    sarah.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})

    home_champion = tom.get("/api/home").get_json()["champion"]
    stats_competitive = tom.get("/api/stats").get_json()["competitive"]

    assert home_champion["points"] == stats_competitive["points"]
    assert home_champion["leader"] == stats_competitive["leader"]
    assert home_champion["is_draw"] == stats_competitive["is_draw"]
    assert home_champion["games_played"] == stats_competitive["games_played"]


def test_home_champion_no_games_played_yet(couple):
    tom = couple["tom"]
    champion = tom.get("/api/home").get_json()["champion"]
    assert champion["games_played"] == 0
    assert champion["leader"] is None
