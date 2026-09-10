"""
Content selection for the Activity system - the counterpart to
services/questions.py, operating on ActivityContent/Activity instead of
Question/Round. Written as genuinely new logic (not a thin wrapper around
the legacy picker) so the new system is actually operative, not decorative.

couple_local_today() is intentionally imported from the legacy module
rather than duplicated - it only depends on couple.timezone, nothing
Round/Question-specific, so there's no reason to have two copies that
could drift.
"""

import random

from app.extensions import db
from app.models import Activity, ActivityContent, ActivityDailySelection
from app.services.questions import couple_local_today  # couple-generic, safe to reuse as-is

__all__ = [
    "pick_content_for_couple",
    "get_or_create_daily_activity",
    "create_random_activity",
    "get_or_create_activity_for_content",
]


def pick_content_for_couple(couple, activity_type="classic_question", category=None, spicy_unlocked_flag=False, exclude_created_by_user_id=None):
    """Choose a piece of content for this couple, preferring content
    they've never played, and avoiding an immediate repeat of their last
    activity. Mirrors services.questions.pick_question_for_couple exactly,
    against the new tables.

    Spicy content policy: while locked, Spicy is fully excluded from any
    unfiltered pool (daily question, general random) - the same as every
    other route that touches Spicy content. Once both partners have
    unlocked it, Spicy behaves as a normal category and is eligible for
    that same unfiltered pool like anything else - no special-casing once
    unlocked.

    exclude_created_by_user_id: for user-generated content (Emoji Story's
    partner-created stories), never serve someone their own creation to
    guess. This is a Python-side filter (payload is JSON, not a queryable
    column) since the couple's own content pool is always small."""
    query = ActivityContent.query.filter_by(activity_type=activity_type, active=True)
    if category:
        if category == "spicy" and not spicy_unlocked_flag:
            return None
        query = query.filter_by(category=category)
    elif not spicy_unlocked_flag:
        # NULL-safe: category != "spicy" alone would, per standard SQL
        # NULL semantics, also exclude every row with category IS NULL
        # (e.g. know_each_other content, which has no category at all) -
        # that's not "excluding spicy," that's excluding anything
        # uncategorized by accident. Be explicit about wanting either.
        query = query.filter(
            db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy")
        )
    # else: spicy_unlocked_flag is True and no specific category was
    # requested - no extra filtering. Spicy content is eligible for the
    # general/daily pool exactly like every other category once unlocked.

    candidates = query.all()
    if exclude_created_by_user_id is not None:
        candidates = [c for c in candidates if c.payload.get("created_by_user_id") != exclude_created_by_user_id]
    if not candidates:
        return None

    played_content_ids = {a.content_id for a in couple.activities.all()}
    unused = [c for c in candidates if c.id not in played_content_ids]
    pool = unused if unused else candidates

    last_activity = couple.activities.order_by(Activity.created_at.desc()).first()
    if last_activity and len(pool) > 1:
        pool = [c for c in pool if c.id != last_activity.content_id] or pool

    return random.choice(pool)


def get_or_create_daily_activity(couple, spicy_unlocked_flag=False):
    """One shared Activity per couple per calendar day, in the couple's
    own timezone. Repeated calls on the same day return the same Activity -
    the exact guarantee the legacy get_or_create_daily_round makes."""
    today = couple_local_today(couple)
    existing = ActivityDailySelection.query.filter_by(couple_id=couple.id, date=today).first()
    if existing and existing.activity is not None:
        return existing.activity
    if existing and existing.activity is None:
        # Defensive: a dangling selection pointing at a since-deleted
        # Activity should never happen in normal operation, but rather
        # than silently returning nothing, replace it and self-heal.
        db.session.delete(existing)
        db.session.flush()

    content = pick_content_for_couple(couple, spicy_unlocked_flag=spicy_unlocked_flag)
    if content is None:
        return None

    activity = Activity(couple_id=couple.id, content_id=content.id, is_daily=True)
    db.session.add(activity)
    db.session.flush()  # need activity.id before creating the ActivityDailySelection row

    daily = ActivityDailySelection(couple_id=couple.id, date=today, content_id=content.id, activity_id=activity.id)
    db.session.add(daily)
    db.session.commit()
    return activity


def create_random_activity(couple, category=None, activity_type="classic_question", spicy_unlocked_flag=False):
    content = pick_content_for_couple(couple, activity_type=activity_type, category=category, spicy_unlocked_flag=spicy_unlocked_flag)
    if content is None:
        return None
    activity = Activity(couple_id=couple.id, content_id=content.id, is_daily=False)
    db.session.add(activity)
    db.session.commit()
    return activity


def get_or_create_activity_for_content(couple, content):
    """Used when a couple deliberately picks a specific piece of content
    (Browse screen) rather than getting a random/daily one. Reuses an
    in-progress (not yet revealed) Activity for the same content instead
    of spawning duplicates if they re-open it - same behaviour as the
    legacy get_or_create_round_for_question."""
    existing = (
        couple.activities.filter_by(content_id=content.id, revealed_at=None)
        .order_by(Activity.created_at.desc())
        .first()
    )
    if existing:
        return existing
    activity = Activity(couple_id=couple.id, content_id=content.id, is_daily=False)
    db.session.add(activity)
    db.session.commit()
    return activity
