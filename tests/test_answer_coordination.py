"""Answer Coordination & Three-Way History - see the build prompt this
was written from. Covers:
  - the core bug fix: a partner's pending answer can now actually be
    completed by the other partner, instead of the content being
    permanently excluded once anyone has an Activity for it
  - mode=unanswered / mode=partner_pending on /api/activities/random
  - cycle-based Play Again (bank_exhausted -> /play-again -> repeat)
  - the three-way /api/activities/history views (mine/mutual/partner)
    and that a partner's answer is never leaked pre-reveal
  - the Browse tab's unanswered_only filter and partner-answered
    discovery endpoint, with the same privacy guarantee
"""

from app.extensions import db
from app.models import ActivityContent


def _create_content(activity_type, category, payload, prompt="Test content"):
    content = ActivityContent(activity_type=activity_type, category=category, prompt=prompt)
    content.payload = payload
    db.session.add(content)
    db.session.commit()
    return content.id


def _wyr_content(app, prompt="Test content"):
    with app.app_context():
        return _create_content(
            "would_you_rather", "normal",
            {"option_a": "Mountains", "option_b": "Beach"},
            prompt=prompt,
        )


# ---------------------------------------------------------------------------
# Core bug fix: mode=unanswered no longer permanently excludes content once
# ANY activity exists for it - only once THIS user has personally answered.
# ---------------------------------------------------------------------------

def test_partner_answering_first_does_not_permanently_hide_content(app, couple):
    """This is the exact bug from the build prompt: Tom answers a WYR,
    and Sarah must still be able to be served that same content (and,
    critically, completing her own Activity reuses Tom's pending one
    instead of creating a duplicate that can never reveal)."""
    tom, sarah = couple["tom"], couple["sarah"]
    _wyr_content(app)

    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 200
    activity = resp.get_json()
    tom.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})

    # Sarah must still be able to draw this same content - the couple-wide
    # exclusion bug would 404 her here with no_content/bank_exhausted.
    resp = sarah.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 200
    sarah_activity = resp.get_json()
    assert sarah_activity["activity_id"] == activity["activity_id"], (
        "Sarah's random draw should reuse Tom's pending Activity, not create a new one"
    )
    assert sarah_activity["my_submitted"] is False
    assert sarah_activity["partner_submitted"] is True
    assert "partner_submission" not in sarah_activity, "partner's answer must stay hidden until Sarah submits too"

    resp = sarah.post(f"/api/activities/{activity['activity_id']}/submit", json={"choice": "a"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["revealed"] is True
    assert data["result"]["outcome"] == "match"


def test_unanswered_mode_excludes_only_my_own_submissions(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    id1 = _wyr_content(app, prompt="Q1")
    _wyr_content(app, prompt="Q2")

    # Tom answers content #1 directly (bypassing random) so we control which one is "used".
    with app.app_context():
        from app.services.activity_questions import get_or_create_activity_for_content
        from app.models import ActivityContent as AC, Couple
        couple_row = Couple.query.first()
        content = AC.query.get(id1)
        activity = get_or_create_activity_for_content(couple_row, content)
        activity_id = activity.id
    tom.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})

    # Tom draws again - must never get content #1 back (he's answered it),
    # only #2 is left. He answers it too, to genuinely exhaust the bank.
    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 200
    assert resp.get_json()["content"]["prompt"] == "Q2"
    tom.post(f"/api/activities/{resp.get_json()['activity_id']}/submit", json={"choice": "a"})

    # A third draw must now report bank_exhausted for Tom, not no_content.
    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "bank_exhausted"

    # Sarah, meanwhile, has answered nothing - both questions are still
    # open to her, including Q1 which Tom has already answered. (She has to
    # submit between draws: an undrawn-but-unanswered question stays
    # eligible, so without submitting, random may legitimately repeat.)
    seen = set()
    for _ in range(2):
        resp = sarah.get("/api/activities/random?activity_type=would_you_rather")
        assert resp.status_code == 200
        data = resp.get_json()
        seen.add(data["content"]["prompt"])
        sarah.post(f"/api/activities/{data['activity_id']}/submit", json={"choice": "b"})
    assert seen == {"Q1", "Q2"}


# ---------------------------------------------------------------------------
# mode=partner_pending
# ---------------------------------------------------------------------------

def test_partner_pending_mode_surfaces_and_completes_pending_activity(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _wyr_content(app)

    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    activity_id = resp.get_json()["activity_id"]
    tom.post(f"/api/activities/{activity_id}/submit", json={"choice": "b"})

    resp = sarah.get("/api/activities/random?activity_type=would_you_rather&mode=partner_pending")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["activity_id"] == activity_id
    assert "partner_submission" not in data

    resp = sarah.post(f"/api/activities/{activity_id}/submit", json={"choice": "b"})
    assert resp.status_code == 201
    assert resp.get_json()["revealed"] is True


def test_partner_pending_mode_says_so_clearly_when_nothing_pending(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _wyr_content(app)

    resp = sarah.get("/api/activities/random?activity_type=would_you_rather&mode=partner_pending")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "no_pending"
    assert "Tom" in data["message"]


# ---------------------------------------------------------------------------
# Cycle-based Play Again
# ---------------------------------------------------------------------------

def test_play_again_starts_a_fresh_cycle_with_no_repeats(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _wyr_content(app, prompt="Only Question")

    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    activity_id = resp.get_json()["activity_id"]
    tom.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})
    # Sarah completes/reveals it too - otherwise the old Activity is still
    # unrevealed and would legitimately be reused rather than replaced.
    sarah.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})

    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "bank_exhausted"

    resp = tom.post("/api/activities/play-again", json={"activity_type": "would_you_rather"})
    assert resp.status_code == 200
    assert resp.get_json()["cycle"] == 2

    # Fresh cycle: the same content is eligible again.
    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 200
    assert resp.get_json()["content"]["prompt"] == "Only Question"

    # And a NEW Activity row was created for this cycle's round (the old
    # one is already revealed, so it can't be reused).
    new_activity_id = resp.get_json()["activity_id"]
    assert new_activity_id != activity_id

    # Answering again exhausts this cycle too - no infinite repeat.
    tom.post(f"/api/activities/{new_activity_id}/submit", json={"choice": "a"})
    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "bank_exhausted"


def test_play_again_does_not_reuse_an_activity_i_already_submitted_to(app, couple):
    """Regression: in cycle 2 the content becomes eligible again, but the
    cycle-1 Activity may still be unrevealed with MY submission on it
    (partner never answered). Reusing that row made the submit fail as a
    duplicate, so the content never counted as answered in the new cycle
    and the same question repeated forever."""
    tom = couple["tom"]
    _wyr_content(app, prompt="Only Question")

    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    first_id = resp.get_json()["activity_id"]
    tom.post(f"/api/activities/{first_id}/submit", json={"choice": "a"})
    # Partner deliberately never answers - the round stays unrevealed.

    tom.post("/api/activities/play-again", json={"activity_type": "would_you_rather"})

    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 200
    second_id = resp.get_json()["activity_id"]
    assert second_id != first_id, "cycle 2 must not reuse an activity I've already submitted to"

    # It must actually accept the submission (the old bug 400'd here)...
    resp = tom.post(f"/api/activities/{second_id}/submit", json={"choice": "b"})
    assert resp.status_code == 201

    # ...and that must genuinely exhaust the cycle, not loop forever.
    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "bank_exhausted"


def test_browse_replay_still_reuses_my_pending_activity(app, couple):
    """The flip side of the above: Browse must NOT get the new-activity
    behaviour. Re-opening a question you already answered should show
    your existing pending round, not silently start a second one."""
    tom = couple["tom"]

    with app.app_context():
        from app.models import Question
        from scripts.migrate_questions_to_activities import migrate
        migrate()
        question = Question.query.filter_by(category="relationship", question_type="free_text").first()
        qid = question.id

    first = tom.post(f"/api/activities/play/{qid}").get_json()["activity_id"]
    tom.post(f"/api/activities/{first}/submit", json={"answer_text": "my answer"})

    second = tom.post(f"/api/activities/play/{qid}").get_json()["activity_id"]
    assert second == first
    assert tom.get(f"/api/activities/{second}").get_json()["my_submitted"] is True


def test_play_again_does_not_affect_the_other_partner(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _wyr_content(app, prompt="Only Question")

    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    activity_id = resp.get_json()["activity_id"]
    tom.post(f"/api/activities/{activity_id}/submit", json={"choice": "a"})
    tom.post("/api/activities/play-again", json={"activity_type": "would_you_rather"})

    # Sarah has never answered - she's not affected by Tom's cycle at all.
    resp = sarah.get("/api/activities/random?activity_type=would_you_rather")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Three-way /api/activities/history
# ---------------------------------------------------------------------------

def test_history_mine_mutual_partner_views(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    _wyr_content(app, prompt="Mutual Q")
    _wyr_content(app, prompt="Partner Only Q")

    # Fully mutual round.
    resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    mutual_id = None
    for _ in range(2):
        data = resp.get_json()
        if data["content"]["prompt"] == "Mutual Q":
            mutual_id = data["activity_id"]
            break
        resp = tom.get("/api/activities/random?activity_type=would_you_rather")
    assert mutual_id is not None
    tom.post(f"/api/activities/{mutual_id}/submit", json={"choice": "a"})
    sarah.post(f"/api/activities/{mutual_id}/submit", json={"choice": "b"})

    # Partner-only pending round: Sarah answers "Partner Only Q", Tom doesn't yet.
    resp = sarah.get("/api/activities/random?activity_type=would_you_rather")
    pending_id = None
    for _ in range(2):
        data = resp.get_json()
        if data["content"]["prompt"] == "Partner Only Q":
            pending_id = data["activity_id"]
            break
        resp = sarah.get("/api/activities/random?activity_type=would_you_rather")
    assert pending_id is not None
    sarah.post(f"/api/activities/{pending_id}/submit", json={"choice": "a"})

    # Tom's "mine": only the mutual one (he hasn't touched the pending one).
    resp = tom.get("/api/activities/history?activity_type=would_you_rather&view=mine")
    assert resp.status_code == 200
    mine_ids = {a["activity_id"] for a in resp.get_json()["activities"]}
    assert mine_ids == {mutual_id}

    # Tom's "mutual": the completed one.
    resp = tom.get("/api/activities/history?activity_type=would_you_rather&view=mutual")
    mutual_ids = {a["activity_id"] for a in resp.get_json()["activities"]}
    assert mutual_ids == {mutual_id}

    # Tom's "partner": Sarah's pending answer, question visible, answer hidden.
    resp = tom.get("/api/activities/history?activity_type=would_you_rather&view=partner")
    assert resp.status_code == 200
    partner_items = resp.get_json()["activities"]
    assert {a["activity_id"] for a in partner_items} == {pending_id}
    item = partner_items[0]
    assert item["content"]["prompt"] == "Partner Only Q"
    assert "partner_submission" not in item
    assert item["my_submitted"] is False

    # Sarah's "partner" view must be empty - she has nothing pending from Tom.
    resp = sarah.get("/api/activities/history?activity_type=would_you_rather&view=partner")
    assert resp.get_json()["activities"] == []


def test_history_rejects_unknown_view(couple):
    tom = couple["tom"]
    resp = tom.get("/api/activities/history?view=bogus")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Browse tab: unanswered_only filter + partner-answered discovery
# ---------------------------------------------------------------------------

def test_questions_unanswered_only_filter(app, couple):
    """Uses the real seeded legacy Question bank via the migration path so
    already_played reflects genuine per-user Activity submissions."""
    tom, sarah = couple["tom"], couple["sarah"]

    with app.app_context():
        from app.models import Question
        from app.services.activity_questions import get_or_create_activity_for_content
        from scripts.migrate_questions_to_activities import migrate
        migrate()
        from app.models import Couple
        couple_row = Couple.query.first()
        question = Question.query.filter_by(category="relationship", question_type="free_text").first()
        from app.models import ActivityContent as AC
        content = AC.query.filter(AC.activity_type == "classic_question").all()
        match = next(c for c in content if c.payload.get("legacy_question_id") == question.id)
        activity = get_or_create_activity_for_content(couple_row, content=match)
        activity_id = activity.id
        target_question_id = question.id

    tom.post(f"/api/activities/{activity_id}/submit", json={"answer_text": "test answer"})

    resp = tom.get("/api/questions?category=relationship")
    all_qs = resp.get_json()["questions"]
    target = next(q for q in all_qs if q["id"] == target_question_id)
    assert target["already_played"] is True

    resp = tom.get("/api/questions?category=relationship&unanswered_only=true")
    unanswered_ids = {q["id"] for q in resp.get_json()["questions"]}
    assert target_question_id not in unanswered_ids

    # Sarah hasn't answered it herself - it must still show up for her,
    # unanswered_only or not (the couple-wide bug this whole feature fixes).
    resp = sarah.get("/api/questions?category=relationship&unanswered_only=true")
    assert target_question_id in {q["id"] for q in resp.get_json()["questions"]}


def test_partner_answered_discovery_endpoint(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]

    with app.app_context():
        from app.models import Question, Couple, ActivityContent as AC
        from app.services.activity_questions import get_or_create_activity_for_content
        from scripts.migrate_questions_to_activities import migrate
        migrate()
        couple_row = Couple.query.first()
        question = Question.query.filter_by(category="relationship", question_type="free_text").first()
        content = AC.query.filter(AC.activity_type == "classic_question").all()
        match = next(c for c in content if c.payload.get("legacy_question_id") == question.id)
        activity = get_or_create_activity_for_content(couple_row, content=match)
        activity_id = activity.id
        target_question_id = question.id

    # Nothing pending yet.
    resp = sarah.get("/api/questions/partner-answered")
    assert resp.get_json()["questions"] == []

    tom.post(f"/api/activities/{activity_id}/submit", json={"answer_text": "tom's answer"})

    resp = sarah.get("/api/questions/partner-answered")
    assert resp.status_code == 200
    items = resp.get_json()["questions"]
    assert any(q["id"] == target_question_id for q in items)

    # Sarah answers via the normal play flow (get_or_create must reuse the
    # same pending Activity, not create a duplicate) and it completes.
    resp = sarah.post(f"/api/activities/play/{target_question_id}")
    assert resp.status_code == 201
    assert resp.get_json()["activity_id"] == activity_id

    resp = sarah.post(f"/api/activities/{activity_id}/submit", json={"answer_text": "sarah's answer"})
    assert resp.status_code == 201
    assert resp.get_json()["revealed"] is True

    # And it's gone from the discovery list now that it's resolved.
    resp = tom.get("/api/questions/partner-answered")
    assert resp.get_json()["questions"] == []
