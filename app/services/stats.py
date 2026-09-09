"""
Building Us Stats page (v1) — Competitive and Together sections.

Source of truth for each half:

  COMPETITIVE — computed from ActivityResult where is_competitive=True,
  plus TwentyQuestionsGame (which never had a persisted point value before
  this — see TWENTY_QUESTIONS_WIN_POINTS below for the new convention).
  Nothing here reads a client-supplied score; every number is a live query
  against stored data, per the Building Us "no hardcoded/manually
  maintained counters" rule.

  KNOWN LIMITATION: Activities migrated from the old Round/Answer engine
  (see scripts/migrate_questions_to_activities.py) never got an
  ActivityResult backfilled — that script deliberately left scoring alone.
  So pre-cutover competitive plays won't count here unless
  scripts/backfill_activity_results.py has been run against this database.

  TOGETHER — "Questions answered" and "Games played" are computed from
  Activity/ActivityContent directly (revealed_at is preserved by the
  migration script), so they reflect full history regardless of whether a
  competitive result was ever computed. Appreciations and Memories are
  from their own dedicated tables (couple.py / memory.py) — no scoring,
  no relationship judgment, per those models' own docstrings.

  Deliberately NOT here: streaks (Phase 7 Task 7.2 — later, calculated
  from actual game history rather than an independent counter that could
  drift), favourites/reactions (were on the old page, not in this spec),
  achievements, or any kind of overall "relationship score."
"""

from app.extensions import db
from app.models import (
    Activity,
    ActivityContent,
    ActivityResult,
    Appreciation,
    CoupleChallenge,
    Memory,
    TwentyQuestionsGame,
)

# 20 Questions has a `status` (won/lost/abandoned) but no points column and
# no scoring logic anywhere in the codebase (checked). This is a new
# convention for the competitive ledger: the winner of the round gets 1
# point, matching the shape of "prediction" scoring elsewhere (+1 correct /
# +0 incorrect) — a 20Q win is, at heart, one partner correctly identifying
# what the other was thinking of. `abandoned` games have no winner and are
# excluded from points/W-L-D entirely (they still count toward Together's
# broad "games played" — see compute_together_stats).
TWENTY_QUESTIONS_WIN_POINTS = 1

# (activity_type, question_type) pairs whose ActivityResult.payload
# ["predictions"][user_id] holds a genuine binary correct/incorrect
# judgement, as opposed to e.g. know_each_other's "rating" subtype, which
# is a partial-credit scale with no meaningful "% correct".
_PREDICTION_ACCURACY_BUCKETS = {
    ("classic_question", "prediction"),
    ("know_each_other", "multiple_choice"),
}


def _competitive_results(couple):
    """Every competitive ActivityResult for this couple, joined to its
    Activity's content (activity_type + question_type), needed to bucket
    prediction-accuracy / would-you-rather-agreement correctly. One query,
    reused for every competitive stat below."""
    return (
        db.session.query(ActivityResult, ActivityContent)
        .join(Activity, ActivityResult.activity_id == Activity.id)
        .join(ActivityContent, Activity.content_id == ActivityContent.id)
        .filter(Activity.couple_id == couple.id, ActivityResult.is_competitive.is_(True))
        .all()
    )


def _twenty_questions_scored(games):
    """See TWENTY_QUESTIONS_WIN_POINTS above. Returns
    (points: {user_id: int}, wins: {user_id: int}, losses: {user_id: int})
    for won/lost games only — abandoned games contribute nothing here."""
    points, wins, losses = {}, {}, {}
    for g in games:
        if g.status not in ("won", "lost"):
            continue
        winner_id = g.guesser_user_id if g.status == "won" else g.chooser_user_id
        loser_id = g.chooser_user_id if g.status == "won" else g.guesser_user_id
        points[winner_id] = points.get(winner_id, 0) + TWENTY_QUESTIONS_WIN_POINTS
        points.setdefault(loser_id, points.get(loser_id, 0))
        wins[winner_id] = wins.get(winner_id, 0) + 1
        losses[loser_id] = losses.get(loser_id, 0) + 1
    return points, wins, losses


def compute_competitive_stats(couple, min_for_percent=5):
    user_a, user_b = couple.ordered_members()
    results = _competitive_results(couple)
    twenty_q_games = TwentyQuestionsGame.query.filter_by(couple_id=couple.id).all()

    points = {user_a.id: 0, user_b.id: 0}
    record = {
        user_a.id: {"wins": 0, "losses": 0, "draws": 0},
        user_b.id: {"wins": 0, "losses": 0, "draws": 0},
    }
    games_played = 0

    prediction_correct = {user_a.id: 0, user_b.id: 0}
    prediction_total = {user_a.id: 0, user_b.id: 0}
    wyr_matches = 0
    wyr_total = 0

    for result, content in results:
        games_played += 1
        result_points = result.points
        a_pts = result_points.get(str(user_a.id), 0)
        b_pts = result_points.get(str(user_b.id), 0)
        points[user_a.id] += a_pts
        points[user_b.id] += b_pts

        if a_pts > b_pts:
            record[user_a.id]["wins"] += 1
            record[user_b.id]["losses"] += 1
        elif b_pts > a_pts:
            record[user_b.id]["wins"] += 1
            record[user_a.id]["losses"] += 1
        else:
            record[user_a.id]["draws"] += 1
            record[user_b.id]["draws"] += 1

        if content.activity_type == "would_you_rather":
            wyr_total += 1
            if result.outcome == "match":
                wyr_matches += 1
        elif (content.activity_type, content.payload.get("question_type")) in _PREDICTION_ACCURACY_BUCKETS:
            for uid_str, info in result.payload.get("predictions", {}).items():
                uid = int(uid_str)
                if uid not in prediction_total:
                    continue
                prediction_total[uid] += 1
                correct = info.get("correct")
                if correct is None:
                    correct = info.get("outcome") == "correct"
                if correct:
                    prediction_correct[uid] += 1

    tq_points, tq_wins, tq_losses = _twenty_questions_scored(twenty_q_games)
    for uid, pts in tq_points.items():
        if uid in points:
            points[uid] += pts
    for uid in record:
        record[uid]["wins"] += tq_wins.get(uid, 0)
        record[uid]["losses"] += tq_losses.get(uid, 0)
    games_played += sum(1 for g in twenty_q_games if g.status in ("won", "lost"))

    if points[user_a.id] == points[user_b.id]:
        leader = None
    else:
        leader = user_a if points[user_a.id] > points[user_b.id] else user_b

    def _pct(correct, total):
        if total < min_for_percent:
            return None
        return round(100 * correct / total)

    return {
        "points": {str(user_a.id): points[user_a.id], str(user_b.id): points[user_b.id]},
        "leader": {"user_id": leader.id, "name": leader.name} if leader else None,
        "is_draw": leader is None and games_played > 0,
        "games_played": games_played,
        "record": {str(user_a.id): record[user_a.id], str(user_b.id): record[user_b.id]},
        "prediction_accuracy": {
            str(uid): {
                "correct": prediction_correct[uid],
                "total": prediction_total[uid],
                "percent": _pct(prediction_correct[uid], prediction_total[uid]),
                "enough_data": prediction_total[uid] >= min_for_percent,
            }
            for uid in (user_a.id, user_b.id)
        },
        "would_you_rather_agreement": {
            "matches": wyr_matches,
            "total": wyr_total,
            "percent": _pct(wyr_matches, wyr_total),
            "enough_data": wyr_total >= min_for_percent,
        },
    }


def compute_together_stats(user):
    couple = user.couple

    activities = (
        db.session.query(Activity, ActivityContent)
        .join(ActivityContent, Activity.content_id == ActivityContent.id)
        .filter(Activity.couple_id == couple.id, Activity.revealed_at.isnot(None))
        .all()
    )
    questions_answered = sum(1 for _, c in activities if c.activity_type == "classic_question")
    activity_games = sum(1 for _, c in activities if c.activity_type != "classic_question")

    challenges_completed = CoupleChallenge.query.filter_by(couple_id=couple.id, status="completed").count()
    twenty_q_completed = TwentyQuestionsGame.query.filter(
        TwentyQuestionsGame.couple_id == couple.id, TwentyQuestionsGame.status != "in_progress"
    ).count()

    appreciations_sent = Appreciation.query.filter_by(couple_id=couple.id, sender_user_id=user.id).count()
    appreciations_received = Appreciation.query.filter_by(couple_id=couple.id, recipient_user_id=user.id).count()

    memories_count = Memory.query.filter_by(couple_id=couple.id).count()

    return {
        "questions_answered": questions_answered,
        "games_played": activity_games + challenges_completed + twenty_q_completed,
        "appreciations": {"sent": appreciations_sent, "received": appreciations_received},
        "memories": memories_count,
    }
