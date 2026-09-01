import random
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.extensions import db
from app.models import DailySelection, Question, Round


def couple_local_today(couple):
    """Today's date in the couple's chosen timezone (falls back to UTC for
    an invalid/unknown tz string rather than 500ing)."""
    try:
        tz = ZoneInfo(couple.timezone or "UTC")
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).date()


def pick_question_for_couple(couple, category=None):
    """Choose a question for this couple, preferring ones they have never
    played, and avoiding an immediate repeat of their last question."""
    query = Question.query.filter_by(active=True)
    if category:
        if category == "spicy" and not _spicy_unlocked(couple):
            return None
        query = query.filter_by(category=category)
    else:
        query = query.filter(Question.category != "spicy")

    candidates = query.all()
    if not candidates:
        return None

    used_ids = {r.question_id for r in couple.rounds}
    unused = [q for q in candidates if q.id not in used_ids]
    pool = unused if unused else candidates

    last_round = couple.rounds.order_by(Round.created_at.desc()).first()
    if last_round and len(pool) > 1:
        pool = [q for q in pool if q.id != last_round.question_id] or pool

    return random.choice(pool)


def _spicy_unlocked(couple):
    members = couple.ordered_members()
    return len(members) == 2 and all(m.spicy_opt_in for m in members)


def get_or_create_daily_round(couple):
    """Every couple gets exactly one shared daily question per calendar day
    (in their own timezone). Calling this repeatedly on the same day always
    returns the same Round."""
    today = couple_local_today(couple)
    existing = DailySelection.query.filter_by(couple_id=couple.id, date=today).first()
    if existing:
        return existing.round

    question = pick_question_for_couple(couple, category=None)
    if question is None:
        return None

    round_ = Round(couple_id=couple.id, question_id=question.id, is_daily=True)
    db.session.add(round_)
    db.session.flush()  # get round_.id before creating the DailySelection row

    daily = DailySelection(couple_id=couple.id, date=today, question_id=question.id, round_id=round_.id)
    db.session.add(daily)
    db.session.commit()
    return round_


def create_random_round(couple, category=None):
    question = pick_question_for_couple(couple, category=category)
    if question is None:
        return None
    round_ = Round(couple_id=couple.id, question_id=question.id, is_daily=False)
    db.session.add(round_)
    db.session.commit()
    return round_


def get_or_create_round_for_question(couple, question):
    """Used when a couple deliberately picks a specific question from the
    Browse screen rather than getting a random/daily one. Reuses an
    in-progress (not yet revealed) round for the same question instead of
    spawning duplicates if they re-open it."""
    existing = (
        couple.rounds.filter_by(question_id=question.id, revealed_at=None)
        .order_by(Round.created_at.desc())
        .first()
    )
    if existing:
        return existing
    round_ = Round(couple_id=couple.id, question_id=question.id, is_daily=False)
    db.session.add(round_)
    db.session.commit()
    return round_
