from app.extensions import db
from app.models import ActivityContent


def _create_content(app, activity_type, category, payload, prompt="Test content", **kwargs):
    with app.app_context():
        content = ActivityContent(activity_type=activity_type, category=category, prompt=prompt, **kwargs)
        content.payload = payload
        db.session.add(content)
        db.session.commit()
        return content.id


def _notif_texts(client):
    return [n["text"] for n in client.get("/api/notifications").get_json()["notifications"]]


def _notif_types(client):
    return [n["type"] for n in client.get("/api/notifications").get_json()["notifications"]]


# ------------------------------------------------------------- game events

def test_game_answered_then_game_ready(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(app, "would_you_rather", "normal", {"option_a": "A", "option_b": "B"})

    activity = tom.get("/api/activities/random?activity_type=would_you_rather").get_json()
    activity_id = activity["activity_id"]

    tom.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})

    # Sarah hasn't gone yet - she gets nudged, Tom gets nothing yet.
    assert "game_answered" in _notif_types(sarah)
    assert "Tom answered" in _notif_texts(sarah)[0] or "answered" in _notif_texts(sarah)[0]
    assert _notif_types(tom) == []

    sarah.post(f"/api/activities/{activity_id}/submit", json={"choice": "b"})

    # Now complete - BOTH get game_ready, and Sarah's earlier nudge is
    # still there too (a real thing that happened, not retracted).
    assert "game_ready" in _notif_types(tom)
    assert "game_ready" in _notif_types(sarah)


def test_game_answered_never_fires_for_spicy(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    content_id = _create_content(app, "would_you_rather", "spicy", {"option_a": "A", "option_b": "B"})
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    activity = tom.get("/api/activities/random?category=spicy&activity_type=would_you_rather").get_json()
    activity_id = activity["activity_id"]
    tom.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})
    assert _notif_types(sarah) == []

    sarah.post(f"/api/activities/{activity_id}/submit", json={"choice": "b"})
    assert _notif_types(tom) == []
    assert _notif_types(sarah) == []


def test_notifications_scoped_to_recipient_only(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(app, "would_you_rather", "normal", {"option_a": "A", "option_b": "B"})
    activity = tom.get("/api/activities/random?activity_type=would_you_rather").get_json()
    tom.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})

    # Only Sarah (the one waiting) got a notification - Tom (who just
    # submitted) shouldn't see a nudge about himself.
    assert len(sarah.get("/api/notifications").get_json()["notifications"]) == 1
    assert len(tom.get("/api/notifications").get_json()["notifications"]) == 0


# ------------------------------------------------------------ appreciation

def test_appreciation_received_notification(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/appreciation/send", json={"message_text": "You're wonderful"})

    assert "appreciation_received" in _notif_types(sarah)
    assert _notif_types(tom) == []


# -------------------------------------------------------------------- plans

def test_plan_added_notification(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/plans", json={"title": "Weekend trip", "category": "trips"})

    assert "plan_added" in _notif_types(sarah)
    assert any("Weekend trip" in t for t in _notif_texts(sarah))
    assert _notif_types(tom) == []


def test_private_plan_never_notifies_partner(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/plans", json={"title": "Surprise", "category": "trips", "is_private": True})

    assert _notif_types(sarah) == []


def test_shared_match_notification(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/plans", json={"title": "Japan trip", "category": "trips"})
    # Tom's own addition shouldn't have triggered a match yet.
    assert "shared_match" not in _notif_types(tom)

    sarah.post("/api/plans", json={"title": "japan TRIP", "category": "trips"})

    # Whitespace/capitalization-tolerant match - both partners notified.
    assert "shared_match" in _notif_types(tom)
    assert "shared_match" in _notif_types(sarah)


def test_duplicate_addition_by_same_person_is_not_a_match(couple):
    tom = couple["tom"]
    tom.post("/api/plans", json={"title": "Japan trip", "category": "trips"})
    tom.post("/api/plans", json={"title": "Japan trip", "category": "trips"})

    assert "shared_match" not in _notif_types(tom)


def test_private_plans_excluded_from_matching_and_notification(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/plans", json={"title": "Japan trip", "category": "trips", "is_private": True})
    sarah.post("/api/plans", json={"title": "Japan trip", "category": "trips"})

    assert "shared_match" not in _notif_types(tom)
    assert "shared_match" not in _notif_types(sarah)


# ---------------------------------------------------------------- champion

def test_new_champion_notification_on_first_win(app, couple):
    """WYR scoring is always symmetric (both matched or neither, see
    WouldYouRatherActivity.compute_result) - agreeing always ties, so
    this specifically verifies a tie never fires new_champion."""
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(app, "would_you_rather", "normal", {"option_a": "A", "option_b": "B"})
    activity = tom.get("/api/activities/random?activity_type=would_you_rather").get_json()
    tom.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})
    sarah.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})

    stats = tom.get("/api/stats").get_json()["competitive"]
    assert stats["leader"] is None  # agreement -> equal points -> tie, by construction
    assert "new_champion" not in _notif_types(tom)
    assert "new_champion" not in _notif_types(sarah)


def _know_each_other_content(app):
    return _create_content(
        app, "know_each_other", "normal",
        {"question_type": "multiple_choice", "options": ["X", "Y", "Z"]},
    )


def test_new_champion_notification_fires_on_real_win(app, couple):
    """know_each_other's prediction scoring is asymmetric - one partner
    can guess correctly while the other doesn't, producing a real
    winner. This is the genuine positive-path test the WYR one above
    can't exercise (WYR can only ever tie)."""
    tom, sarah = couple["tom"], couple["sarah"]
    _know_each_other_content(app)
    activity = tom.get("/api/activities/random?activity_type=know_each_other").get_json()
    activity_id = activity["activity_id"]
    # Tom guesses Sarah correctly; Sarah guesses Tom incorrectly - Tom wins 1-0.
    tom.post(f"/api/activities/{activity_id}/submit", json={"answer_option": "X", "predicted_option": "Y"})
    sarah.post(f"/api/activities/{activity_id}/submit", json={"answer_option": "Y", "predicted_option": "Z"})

    stats = tom.get("/api/stats").get_json()["competitive"]
    assert stats["leader"]["name"] == "Tom"
    assert "new_champion" in _notif_types(tom)
    assert "new_champion" in _notif_types(sarah)
    assert any("Tom" in t for t in _notif_texts(tom) if "champion" in t.lower())


def test_new_champion_does_not_refire_for_unchanged_leader(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]

    for _ in range(2):
        _know_each_other_content(app)
        activity = tom.get("/api/activities/random?activity_type=know_each_other").get_json()
        activity_id = activity["activity_id"]
        # Same pattern each round - Tom wins both, stays champion throughout.
        tom.post(f"/api/activities/{activity_id}/submit", json={"answer_option": "X", "predicted_option": "Y"})
        sarah.post(f"/api/activities/{activity_id}/submit", json={"answer_option": "Y", "predicted_option": "Z"})

    stats = tom.get("/api/stats").get_json()["competitive"]
    assert stats["leader"]["name"] == "Tom"
    champion_count = _notif_types(tom).count("new_champion")
    assert champion_count == 1  # crowned once, not re-announced for staying champion


def test_champion_events_excluded_for_spicy(app, couple):
    """A Spicy activity never contributes competitive points at all (see
    app/services/stats.py), so it must never be able to trigger a
    new_champion notification either."""
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(app, "would_you_rather", "spicy", {"option_a": "A", "option_b": "B"})
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    activity = tom.get("/api/activities/random?category=spicy&activity_type=would_you_rather").get_json()
    tom.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})
    sarah.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "b"})

    assert "new_champion" not in _notif_types(tom)
    assert "new_champion" not in _notif_types(sarah)


# ----------------------------------------------------------- list/mark seen

def test_list_and_unseen_count(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/appreciation/send", json={"message_text": "hi"})
    tom.post("/api/plans", json={"title": "Trip", "category": "trips"})

    data = sarah.get("/api/notifications").get_json()
    assert data["unseen_count"] == 2
    assert len(data["notifications"]) == 2
    assert all(n["is_seen"] is False for n in data["notifications"])


def test_mark_all_seen(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/appreciation/send", json={"message_text": "hi"})

    assert sarah.get("/api/notifications").get_json()["unseen_count"] == 1

    resp = sarah.post("/api/notifications/seen")
    assert resp.status_code == 200

    data = sarah.get("/api/notifications").get_json()
    assert data["unseen_count"] == 0
    assert all(n["is_seen"] is True for n in data["notifications"])


def test_notification_text_is_concise(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/plans", json={"title": "x" * 300, "category": "trips"})

    text = sarah.get("/api/notifications").get_json()["notifications"][0]["text"]
    assert len(text) <= 140


def test_notifications_require_login(client):
    resp = client.get("/api/notifications")
    assert resp.status_code == 401
