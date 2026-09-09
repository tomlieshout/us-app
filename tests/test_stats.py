from datetime import datetime

from app.extensions import db
from app.models import (
    Activity,
    ActivityContent,
    Appreciation,
    CoupleChallenge,
    Couple,
    Memory,
    TwentyQuestionsGame,
    User,
)
from scripts.backfill_activity_results import backfill


def _user_ids(app):
    with app.app_context():
        tom_id = User.query.filter_by(username="tom").first().id
        sarah_id = User.query.filter_by(username="sarah").first().id
        couple_id = Couple.query.first().id
    return tom_id, sarah_id, couple_id


def _create_activity(app, couple_id, activity_type, payload=None, category=None, prompt="Test prompt"):
    with app.app_context():
        content = ActivityContent(activity_type=activity_type, category=category, prompt=prompt)
        content.payload = payload or {}
        db.session.add(content)
        db.session.flush()
        activity = Activity(couple_id=couple_id, content_id=content.id)
        db.session.add(activity)
        db.session.commit()
        return activity.id


def _submit(client, activity_id, payload):
    resp = client.post(f"/api/activities/{activity_id}/submit", json=payload)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def _get_stats(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    return resp.get_json()


# ---------------------------------------------------------------- empty state

def test_empty_state_no_crash(app, couple):
    tom = couple["tom"]
    stats = _get_stats(tom)

    comp = stats["competitive"]
    assert comp["points"] == {str(_id): 0 for _id in _user_ids(app)[:2]}
    assert comp["leader"] is None
    assert comp["is_draw"] is False
    assert comp["games_played"] == 0
    assert stats["together"]["questions_answered"] == 0
    assert stats["together"]["games_played"] == 0
    assert stats["together"]["appreciations"] == {"sent": 0, "received": 0}
    assert stats["together"]["memories"] == 0


# ------------------------------------------------------ would you rather

def test_would_you_rather_match_and_no_match(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    match_id = _create_activity(app, couple_id, "would_you_rather", {"option_a": "Beach", "option_b": "Mountains"})
    _submit(tom, match_id, {"choice": "a"})
    _submit(sarah, match_id, {"choice": "a"})

    no_match_id = _create_activity(app, couple_id, "would_you_rather", {"option_a": "Beach", "option_b": "Mountains"})
    _submit(tom, no_match_id, {"choice": "a"})
    _submit(sarah, no_match_id, {"choice": "b"})

    stats = _get_stats(tom)
    comp = stats["competitive"]

    assert comp["points"][str(tom_id)] == 1
    assert comp["points"][str(sarah_id)] == 1
    assert comp["games_played"] == 2
    # exact_match scoring always awards both partners the same points, so a
    # would_you_rather activity can never individually produce a win/loss.
    assert comp["record"][str(tom_id)] == {"wins": 0, "losses": 0, "draws": 2}
    assert comp["leader"] is None
    assert comp["is_draw"] is True

    wyr = comp["would_you_rather_agreement"]
    assert wyr["matches"] == 1
    assert wyr["total"] == 2
    # below the 5-round minimum -> percent withheld, same UX rule as prediction%
    assert wyr["enough_data"] is False
    assert wyr["percent"] is None


# ------------------------------------------------------- classic prediction

def _play_classic_prediction(app, couple_id, tom, sarah, tom_id, sarah_id, tom_correct, sarah_correct):
    activity_id = _create_activity(
        app, couple_id, "classic_question", {"question_type": "prediction", "options": ["A", "B", "C"]}
    )
    tom_real, sarah_real = "A", "B"
    tom_predicted = sarah_real if tom_correct else "C"
    sarah_predicted = tom_real if sarah_correct else "C"
    _submit(tom, activity_id, {"answer_option": tom_real, "predicted_option": tom_predicted})
    _submit(sarah, activity_id, {"answer_option": sarah_real, "predicted_option": sarah_predicted})
    return activity_id


def test_classic_prediction_scoring_and_accuracy(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    # Tom correct 4/5, Sarah correct 2/5 - both above the 5-round minimum.
    outcomes = [(True, True), (True, False), (True, True), (True, False), (False, True)]
    for tom_correct, sarah_correct in outcomes:
        _play_classic_prediction(app, couple_id, tom, sarah, tom_id, sarah_id, tom_correct, sarah_correct)

    stats = _get_stats(tom)
    comp = stats["competitive"]

    tom_acc = comp["prediction_accuracy"][str(tom_id)]
    sarah_acc = comp["prediction_accuracy"][str(sarah_id)]
    assert tom_acc == {"correct": 4, "total": 5, "percent": 80, "enough_data": True}
    assert sarah_acc == {"correct": 3, "total": 5, "percent": 60, "enough_data": True}

    # points: 1 each time you personally guessed correctly
    assert comp["points"][str(tom_id)] == 4
    assert comp["points"][str(sarah_id)] == 3
    assert comp["games_played"] == 5
    assert comp["leader"] == {"user_id": tom_id, "name": "Tom"}
    assert comp["is_draw"] is False

    # per-round win/loss: (T,T)=draw 1-1, (T,F)=tom win, (T,T)=draw, (T,F)=tom win, (F,T)=sarah win
    assert comp["record"][str(tom_id)] == {"wins": 2, "losses": 1, "draws": 2}
    assert comp["record"][str(sarah_id)] == {"wins": 1, "losses": 2, "draws": 2}


def test_classic_prediction_below_minimum_hides_percent(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    for _ in range(3):
        _play_classic_prediction(app, couple_id, tom, sarah, tom_id, sarah_id, True, True)

    stats = _get_stats(tom)
    tom_acc = stats["competitive"]["prediction_accuracy"][str(tom_id)]
    assert tom_acc["total"] == 3
    assert tom_acc["enough_data"] is False
    assert tom_acc["percent"] is None


# ------------------------------------------------ classic multiple_choice / rating

def test_classic_multiple_choice_is_always_a_draw(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    activity_id = _create_activity(
        app, couple_id, "classic_question", {"question_type": "multiple_choice", "options": ["Pizza", "Sushi"]}
    )
    _submit(tom, activity_id, {"answer_option": "Pizza"})
    _submit(sarah, activity_id, {"answer_option": "Sushi"})

    stats = _get_stats(tom)
    comp = stats["competitive"]
    assert comp["points"][str(tom_id)] == 0
    assert comp["points"][str(sarah_id)] == 0
    assert comp["record"][str(tom_id)] == {"wins": 0, "losses": 0, "draws": 1}
    # not a prediction and not would_you_rather -> excluded from both % stats
    assert comp["prediction_accuracy"][str(tom_id)]["total"] == 0
    assert comp["would_you_rather_agreement"]["total"] == 0


def test_classic_free_text_is_not_competitive_but_counts_as_question_answered(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    activity_id = _create_activity(app, couple_id, "classic_question", {"question_type": "free_text"})
    _submit(tom, activity_id, {"answer_text": "Paris"})
    _submit(sarah, activity_id, {"answer_text": "Tokyo"})

    stats = _get_stats(tom)
    assert stats["competitive"]["games_played"] == 0
    assert stats["competitive"]["points"][str(tom_id)] == 0
    assert stats["together"]["questions_answered"] == 1
    assert stats["together"]["games_played"] == 0


# ------------------------------------------------------------ know each other

def test_know_each_other_multiple_choice_counts_toward_prediction_accuracy(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    activity_id = _create_activity(
        app, couple_id, "know_each_other", {"question_type": "multiple_choice", "options": ["Coffee", "Tea"]}
    )
    # tom predicts sarah correctly, sarah predicts tom incorrectly
    _submit(tom, activity_id, {"answer_option": "Coffee", "predicted_option": "Tea"})
    _submit(sarah, activity_id, {"answer_option": "Tea", "predicted_option": "Tea"})

    stats = _get_stats(tom)
    comp = stats["competitive"]
    assert comp["prediction_accuracy"][str(tom_id)]["total"] == 1
    assert comp["prediction_accuracy"][str(tom_id)]["correct"] == 1
    assert comp["prediction_accuracy"][str(sarah_id)]["total"] == 1
    assert comp["prediction_accuracy"][str(sarah_id)]["correct"] == 0


def test_know_each_other_rating_excluded_from_prediction_accuracy(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    activity_id = _create_activity(
        app, couple_id, "know_each_other", {"question_type": "rating", "options": [str(n) for n in range(1, 11)]}
    )
    _submit(tom, activity_id, {"answer_option": "7", "predicted_option": "8"})
    _submit(sarah, activity_id, {"answer_option": "8", "predicted_option": "7"})

    stats = _get_stats(tom)
    comp = stats["competitive"]
    # rating is a partial-credit scale, not a binary prediction - excluded
    assert comp["prediction_accuracy"][str(tom_id)]["total"] == 0
    assert comp["prediction_accuracy"][str(sarah_id)]["total"] == 0
    # but it still contributes points and a games_played count
    assert comp["games_played"] == 1
    assert comp["points"][str(tom_id)] == comp["points"][str(sarah_id)]  # rating_difference is symmetric


# ------------------------------------------------------- non-competitive games

def test_non_competitive_activity_excluded_from_competitive_counted_in_together(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    activity_id = _create_activity(app, couple_id, "who_would", {}, prompt="Who would forget an anniversary?")
    _submit(tom, activity_id, {"choice": "me"})
    _submit(sarah, activity_id, {"choice": "partner"})

    stats = _get_stats(tom)
    assert stats["competitive"]["games_played"] == 0
    assert stats["competitive"]["points"][str(tom_id)] == 0
    assert stats["together"]["games_played"] == 1
    assert stats["together"]["questions_answered"] == 0


# ---------------------------------------------------------------- 20 questions

def test_twenty_questions_scoring_and_abandoned_exclusion(app, couple):
    tom_id, sarah_id, couple_id = _user_ids(app)

    with app.app_context():
        won = TwentyQuestionsGame(
            couple_id=couple_id, chooser_user_id=tom_id, guesser_user_id=sarah_id,
            secret_category="thing", secret_text="a kite", status="won", completed_at=datetime.utcnow(),
        )
        lost = TwentyQuestionsGame(
            couple_id=couple_id, chooser_user_id=sarah_id, guesser_user_id=tom_id,
            secret_category="person", secret_text="a friend", status="lost", completed_at=datetime.utcnow(),
        )
        abandoned = TwentyQuestionsGame(
            couple_id=couple_id, chooser_user_id=tom_id, guesser_user_id=sarah_id,
            secret_category="place", secret_text="a beach", status="abandoned", completed_at=datetime.utcnow(),
        )
        db.session.add_all([won, lost, abandoned])
        db.session.commit()

    tom = couple["tom"]
    stats = _get_stats(tom)
    comp = stats["competitive"]

    # game 1 ("won"): sarah is guesser and wins -> sarah +1, tom +0
    # game 2 ("lost"): tom is guesser and loses -> sarah (chooser) wins -> sarah +1, tom +0
    assert comp["points"][str(sarah_id)] == 2
    assert comp["points"][str(tom_id)] == 0
    assert comp["record"][str(sarah_id)] == {"wins": 2, "losses": 0, "draws": 0}
    assert comp["record"][str(tom_id)] == {"wins": 0, "losses": 2, "draws": 0}
    # abandoned excluded from competitive games_played...
    assert comp["games_played"] == 2
    # ...but still counted in Together's broad games_played (all 3 completed states)
    assert stats["together"]["games_played"] == 3


# ------------------------------------------------ challenges / appreciation / memories

def test_together_challenges_appreciations_memories(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom_id, sarah_id, couple_id = _user_ids(app)

    with app.app_context():
        content = ActivityContent(activity_type="classic_question", prompt="challenge bank entry")
        content.payload = {}
        db.session.add(content)
        db.session.flush()
        completed = CoupleChallenge(couple_id=couple_id, content_id=content.id, status="completed")
        accepted_only = ActivityContent(activity_type="classic_question", prompt="another challenge entry")
        accepted_only.payload = {}
        db.session.add(accepted_only)
        db.session.flush()
        not_completed = CoupleChallenge(couple_id=couple_id, content_id=accepted_only.id, status="accepted")
        db.session.add_all([completed, not_completed])

        db.session.add(Appreciation(couple_id=couple_id, sender_user_id=tom_id, recipient_user_id=sarah_id, message_text="You're great"))
        db.session.add(Appreciation(couple_id=couple_id, sender_user_id=sarah_id, recipient_user_id=tom_id, message_text="So are you"))
        db.session.add(Appreciation(couple_id=couple_id, sender_user_id=sarah_id, recipient_user_id=tom_id, message_text="Really!"))

        db.session.add(Memory(couple_id=couple_id, created_by_id=tom_id, title="Our first trip"))
        db.session.commit()

    tom_stats = _get_stats(tom)["together"]
    sarah_stats = _get_stats(sarah)["together"]

    assert tom_stats["games_played"] == 1  # only the completed challenge counts
    assert tom_stats["appreciations"] == {"sent": 1, "received": 2}
    assert sarah_stats["appreciations"] == {"sent": 2, "received": 1}
    assert tom_stats["memories"] == 1
    assert sarah_stats["memories"] == 1


# ------------------------------------------------------------------ backfill

def test_backfill_scores_migrated_activities_idempotently(app, couple):
    tom_id, sarah_id, couple_id = _user_ids(app)

    # Simulate what migrate_questions_to_activities.py leaves behind: a
    # complete, revealed Activity with real submissions but no
    # ActivityResult (deliberately not backfilled by that script).
    with app.app_context():
        from app.models import ActivitySubmission

        content = ActivityContent(activity_type="classic_question", prompt="legacy prediction")
        content.payload = {"question_type": "prediction", "options": ["A", "B"], "legacy_question_id": 999}
        db.session.add(content)
        db.session.flush()

        activity = Activity(couple_id=couple_id, content_id=content.id, revealed_at=datetime.utcnow())
        activity.state = {"legacy_round_id": 999}
        db.session.add(activity)
        db.session.flush()

        sub_tom = ActivitySubmission(activity_id=activity.id, user_id=tom_id)
        sub_tom.payload = {"answer_option": "A", "predicted_option": "B"}
        sub_sarah = ActivitySubmission(activity_id=activity.id, user_id=sarah_id)
        sub_sarah.payload = {"answer_option": "B", "predicted_option": "A"}
        db.session.add_all([sub_tom, sub_sarah])
        db.session.commit()
        activity_id = activity.id

    tom = couple["tom"]
    before = _get_stats(tom)["competitive"]
    assert before["games_played"] == 0  # not scored yet - the known v1 gap

    with app.app_context():
        result_stats = backfill()
        db.session.commit()

    assert result_stats["scored"] == 1
    assert result_stats["skipped_incomplete"] == 0

    after = _get_stats(tom)["competitive"]
    assert after["games_played"] == 1
    assert after["points"][str(tom_id)] == 1  # A predicted B, B was sarah's real answer -> correct
    assert after["points"][str(sarah_id)] == 1  # B predicted A, A was tom's real answer -> correct

    # re-running is a no-op: the candidate is already scored now
    with app.app_context():
        second_run = backfill()
    assert second_run["candidates"] == 0
    assert second_run["scored"] == 0


def test_backfill_skips_incomplete_activities(app, couple):
    tom_id, sarah_id, couple_id = _user_ids(app)

    with app.app_context():
        from app.models import ActivitySubmission

        content = ActivityContent(activity_type="classic_question", prompt="legacy incomplete")
        content.payload = {"question_type": "prediction", "options": ["A", "B"]}
        db.session.add(content)
        db.session.flush()

        # revealed_at set but only one partner ever answered - shouldn't
        # happen from the real migration script (it preserves revealed_at
        # as None for genuinely-unrevealed rounds), but the backfill script
        # should never crash or fabricate a result if it does.
        activity = Activity(couple_id=couple_id, content_id=content.id, revealed_at=datetime.utcnow())
        db.session.add(activity)
        db.session.flush()
        sub_tom = ActivitySubmission(activity_id=activity.id, user_id=tom_id)
        sub_tom.payload = {"answer_option": "A", "predicted_option": "B"}
        db.session.add(sub_tom)
        db.session.commit()

    with app.app_context():
        stats_out = backfill()
        db.session.rollback()

    assert stats_out["skipped_incomplete"] == 1
    assert stats_out["scored"] == 0
