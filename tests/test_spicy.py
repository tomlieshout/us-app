from app.extensions import db
from app.models import ActivityContent


def _create_content(app, activity_type, category, payload):
    """conftest's `app` fixture only seeds the legacy Question bank (see
    _seed_test_questions), not ActivityContent - same convention
    test_stats.py already established for Activity-system tests. Returns
    the new content's id."""
    with app.app_context():
        content = ActivityContent(activity_type=activity_type, category=category, prompt="Test content")
        content.payload = payload
        db.session.add(content)
        db.session.commit()
        return content.id


def test_spicy_locked_by_default(couple):
    tom = couple["tom"]
    resp = tom.get("/api/questions?category=spicy")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "spicy_locked"

    resp = tom.get("/api/rounds/random?category=spicy")
    assert resp.status_code == 403


def test_spicy_requires_both_partners_to_opt_in(couple):
    tom, sarah = couple["tom"], couple["sarah"]

    resp = tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    assert resp.status_code == 200
    assert resp.get_json()["couple"]["spicy_unlocked"] is False  # Sarah hasn't opted in yet

    resp = tom.get("/api/questions?category=spicy")
    assert resp.status_code == 403

    resp = sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    assert resp.get_json()["couple"]["spicy_unlocked"] is True

    resp = tom.get("/api/questions?category=spicy")
    assert resp.status_code == 200
    assert len(resp.get_json()["questions"]) > 0


def test_spicy_opt_in_requires_adult_confirmation(couple):
    tom = couple["tom"]
    resp = tom.post("/api/settings/spicy", json={"enabled": True})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "confirmation_required"


def test_either_partner_can_disable_spicy(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    resp = sarah.post("/api/settings/spicy", json={"enabled": False})
    assert resp.get_json()["couple"]["spicy_unlocked"] is False

    resp = tom.get("/api/questions?category=spicy")
    assert resp.status_code == 403


def test_private_spicy_answer_hidden_from_partner(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    questions = tom.get("/api/questions?category=spicy").get_json()["questions"]
    free_text_q = next(q for q in questions if q["question_type"] == "free_text")

    played = tom.post(f"/api/questions/{free_text_q['id']}/play").get_json()
    round_id = played["round_id"]

    tom.post("/api/answers", json={"round_id": round_id, "answer_text": "Something private", "is_private": True})
    sarah.post("/api/answers", json={"round_id": round_id, "answer_text": "My honest answer"})

    sarah_view = sarah.get(f"/api/rounds/{round_id}").get_json()
    assert sarah_view["partner_answer"]["is_private"] is True
    assert "text" not in sarah_view["partner_answer"]
    assert "Something private" not in str(sarah_view)

    # Tom can still see his own answer content
    tom_view = tom.get(f"/api/rounds/{round_id}").get_json()
    assert tom_view["my_answer"]["text"] == "Something private"


def test_legacy_history_and_questions_include_spicy_only_when_unlocked(couple):
    """Regression test for a real bug: /api/rounds/history and
    /api/questions unconditionally excluded category="spicy", even once
    unlocked, instead of only excluding it while locked. Spicy must behave
    as a fully normal category - including in unfiltered "All" views -
    once both partners have opted in."""
    tom, sarah = couple["tom"], couple["sarah"]

    resp = tom.get("/api/rounds/history?category=spicy")
    assert resp.status_code == 403

    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    questions = tom.get("/api/questions?category=spicy").get_json()["questions"]
    free_text_q = next(q for q in questions if q["question_type"] == "free_text")
    played = tom.post(f"/api/questions/{free_text_q['id']}/play").get_json()
    round_id = played["round_id"]
    tom.post("/api/answers", json={"round_id": round_id, "answer_text": "Tom's answer"})
    sarah.post("/api/answers", json={"round_id": round_id, "answer_text": "Sarah's answer"})

    # Unlocked: unfiltered "All" history includes it, and the bank browse
    # includes spicy questions even with no category filter.
    all_history = tom.get("/api/rounds/history").get_json()["rounds"]
    assert any(r["round_id"] == round_id for r in all_history)
    all_questions = tom.get("/api/questions").get_json()["questions"]
    assert any(q["category"] == "spicy" for q in all_questions)

    sarah.post("/api/settings/spicy", json={"enabled": False})

    # Locked again: unfiltered views exclude it, explicit filter 403s.
    all_history = tom.get("/api/rounds/history").get_json()["rounds"]
    assert not any(r["round_id"] == round_id for r in all_history)
    all_questions = tom.get("/api/questions").get_json()["questions"]
    assert not any(q["category"] == "spicy" for q in all_questions)
    assert tom.get("/api/rounds/history?category=spicy").status_code == 403


def test_spicy_multiple_choice_question_playable_once_unlocked(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    questions = tom.get("/api/questions?category=spicy").get_json()["questions"]
    mc_q = next(q for q in questions if q["question_type"] == "multiple_choice")

    played = tom.post(f"/api/questions/{mc_q['id']}/play").get_json()
    round_id = played["round_id"]

    tom.post("/api/answers", json={"round_id": round_id, "answer_option": mc_q["options"][0]})
    resp = sarah.post("/api/answers", json={"round_id": round_id, "answer_option": mc_q["options"][-1]})
    assert resp.status_code == 201
    assert resp.get_json()["revealed"] is True


def test_spicy_prediction_question_playable_once_unlocked(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    questions = tom.get("/api/questions?category=spicy").get_json()["questions"]
    prediction_q = next(q for q in questions if q["question_type"] == "prediction")

    played = tom.post(f"/api/questions/{prediction_q['id']}/play").get_json()
    round_id = played["round_id"]

    option, predicted = prediction_q["options"][0], prediction_q["options"][-1]
    tom.post("/api/answers", json={"round_id": round_id, "answer_option": option, "predicted_option": predicted})
    resp = sarah.post("/api/answers", json={"round_id": round_id, "answer_option": predicted, "predicted_option": option})
    assert resp.status_code == 201
    assert resp.get_json()["revealed"] is True


def test_spicy_would_you_rather_hidden_while_locked_normal_once_unlocked(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    content_id = _create_content(app, "would_you_rather", "spicy", {"option_a": "A", "option_b": "B"})

    resp = tom.get("/api/activities/random?category=spicy&activity_type=would_you_rather")
    assert resp.status_code == 403

    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    activity = tom.get("/api/activities/random?category=spicy&activity_type=would_you_rather").get_json()
    activity_id = activity["activity_id"]
    assert activity["content"]["id"] == content_id
    tom.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})
    sarah.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})

    assert tom.get(f"/api/activities/{activity_id}").status_code == 200
    all_history = tom.get("/api/activities/history").get_json()["activities"]
    assert any(a["activity_id"] == activity_id for a in all_history)

    sarah.post("/api/settings/spicy", json={"enabled": False})

    assert tom.get(f"/api/activities/{activity_id}").status_code == 404
    all_history = tom.get("/api/activities/history").get_json()["activities"]
    assert not any(a["activity_id"] == activity_id for a in all_history)
    assert tom.get("/api/activities/history?category=spicy").status_code == 403

    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    assert tom.get(f"/api/activities/{activity_id}").status_code == 200
    all_history = tom.get("/api/activities/history").get_json()["activities"]
    assert any(a["activity_id"] == activity_id for a in all_history)


def test_challenges_spicy_gated_on_random_and_accept(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(app, "challenge", "spicy", {"requires_both": False})

    resp = tom.get("/api/challenges/random?category=spicy")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "spicy_locked"

    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    content = tom.get("/api/challenges/random?category=spicy").get_json()
    assert content["category"] == "spicy"
    resp = tom.post("/api/challenges/accept", json={"content_id": content["id"]})
    assert resp.status_code == 201

    sarah.post("/api/settings/spicy", json={"enabled": False})

    # Re-locked: even re-accepting the same already-accepted content_id
    # (the idempotent-existing-row shortcut) must not bypass the gate.
    resp = tom.post("/api/challenges/accept", json={"content_id": content["id"]})
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "spicy_locked"


def test_challenges_unfiltered_random_never_surfaces_spicy_while_locked(app, couple):
    tom = couple["tom"]
    _create_content(app, "challenge", "spicy", {"requires_both": False})
    _create_content(app, "challenge", "cute", {"requires_both": False})
    for _ in range(30):
        resp = tom.get("/api/challenges/random")
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.get_json()["category"] != "spicy"


def test_challenges_mine_spicy_only_via_explicit_category_filter(app, couple):
    """Challenges deliberately diverges from the rest of the app here:
    unlike Questions/Activities (where Spicy behaves as a normal category
    in unfiltered "All" once unlocked), Challenges NEVER surfaces Spicy in
    the unfiltered /mine list, regardless of lock state - only the
    explicit category="spicy" filter (the dedicated Spicy tab) ever shows
    it, and that still requires unlocked. See list_challenges' docstring."""
    tom, sarah = couple["tom"], couple["sarah"]
    content_id = _create_content(app, "challenge", "spicy", {"requires_both": False})
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    accepted = tom.post("/api/challenges/accept", json={"content_id": content_id}).get_json()
    challenge_id = accepted["id"]

    # Unfiltered "mine" never includes it, unlocked or not.
    mine = tom.get("/api/challenges/mine").get_json()["challenges"]
    assert not any(c["id"] == challenge_id for c in mine)

    # The explicit Spicy-tab filter does show it, while unlocked...
    mine_spicy = tom.get("/api/challenges/mine?category=spicy").get_json()["challenges"]
    assert any(c["id"] == challenge_id for c in mine_spicy)

    # ...and correctly 403s once locked again, same as every other
    # spicy-gated endpoint.
    sarah.post("/api/settings/spicy", json={"enabled": False})
    resp = tom.get("/api/challenges/mine?category=spicy")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "spicy_locked"


def test_challenges_complete_blocked_if_relocked_after_accept(app, couple):
    """Second-order-leak protection: a challenge accepted while unlocked
    must not be completable while locked, even though the accept itself
    already happened."""
    tom, sarah = couple["tom"], couple["sarah"]
    content_id = _create_content(app, "challenge", "spicy", {"requires_both": False})
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    accepted = tom.post("/api/challenges/accept", json={"content_id": content_id}).get_json()

    sarah.post("/api/settings/spicy", json={"enabled": False})

    resp = tom.post(f"/api/challenges/{accepted['id']}/complete")
    assert resp.status_code == 404


def test_stats_exclude_spicy_activity_and_challenges(app, couple):
    """Spicy content must never move the general Stats numbers -
    points/leader/W-L-D/prediction accuracy/WYR agreement and Together's
    games_played should be unaffected by Spicy plays, regardless of lock
    state, per the Spicy brief's Stats-previews carve-out."""
    tom, sarah = couple["tom"], couple["sarah"]
    _create_content(app, "would_you_rather", "spicy", {"option_a": "A", "option_b": "B"})
    challenge_content_id = _create_content(app, "challenge", "spicy", {"requires_both": False})
    _create_content(app, "would_you_rather", "normal", {"option_a": "A", "option_b": "B"})

    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    baseline = tom.get("/api/stats").get_json()

    activity = tom.get("/api/activities/random?category=spicy&activity_type=would_you_rather").get_json()
    activity_id = activity["activity_id"]
    tom.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})
    sarah.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})

    accepted = tom.post("/api/challenges/accept", json={"content_id": challenge_content_id}).get_json()
    tom.post(f"/api/challenges/{accepted['id']}/complete")

    after_spicy = tom.get("/api/stats").get_json()
    assert after_spicy["competitive"] == baseline["competitive"]
    assert after_spicy["together"]["games_played"] == baseline["together"]["games_played"]

    # Positive control: a non-spicy Would You Rather DOES move the
    # numbers, so this isn't vacuously passing due to a broken query.
    normal_activity = tom.get("/api/activities/random?activity_type=would_you_rather&category=normal").get_json()
    normal_id = normal_activity["activity_id"]
    tom.post(f"/api/activities/{normal_id}/submit", json={"choice": "a"})
    sarah.post(f"/api/activities/{normal_id}/submit", json={"choice": "a"})

    after_normal = tom.get("/api/stats").get_json()
    assert after_normal["competitive"]["games_played"] == baseline["competitive"]["games_played"] + 1
    assert after_normal["together"]["games_played"] == baseline["together"]["games_played"] + 1
