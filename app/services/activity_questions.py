"""
Content selection for the Activity system - the counterpart to
services/questions.py, operating on ActivityContent/Activity instead of
Question/Round. Written as genuinely new logic (not a thin wrapper around
the legacy picker) so the new system is actually operative, not decorative.

couple_local_today() is intentionally imported from the legacy module
rather than duplicated - it only depends on couple.timezone, nothing
Round/Question-specific, so there's no reason to have two copies that
could drift.

Answer Coordination & cycles (added alongside the toggle/Past Answers
build): pick_content_for_couple()/get_or_create_daily_activity() are
UNCHANGED and still couple-wide on purpose - the shared daily pick is
genuinely one question for the whole couple, and "don't repeat a question
the couple has already seen today-and-before" is the correct behaviour
there, not a bug. The bug was specific to create_random_activity(), used
by each game's own "give me something to answer" flow: it excluded
content based on whether *any* Activity row existed for it, so once one
partner answered something, the other could never be served it (and
could never complete/reveal it) either. pick_content_for_user() is the
fixed, per-user replacement used there - "already answered" is scoped to
what *this* user has personally submitted, not what the couple has
touched at all.
"""

import random

from app.extensions import db
from app.models import Activity, ActivityContent, ActivityCycle, ActivityDailySelection, ActivitySubmission
from app.services.questions import couple_local_today  # couple-generic, safe to reuse as-is

__all__ = [
    "pick_content_for_couple",
    "get_or_create_daily_activity",
    "create_random_activity",
    "get_or_create_activity_for_content",
    "get_current_cycle",
    "advance_cycle",
    "bank_has_any_content",
    "pick_content_for_user",
    "find_partner_pending_activity",
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


def get_or_create_daily_activity(couple, spicy_unlocked_flag=False, activity_type="classic_question"):
    """One shared Activity per couple per calendar day, in the couple's
    own timezone. Repeated calls on the same day return the same Activity -
    the exact guarantee the legacy get_or_create_daily_round makes.

    activity_type defaults to "classic_question" (unchanged from before) so
    the existing /api/activities/current route's behavior is untouched -
    it never passes this argument. Home's daily-rotation (see
    app/services/home.py) is the only caller that passes something else,
    reusing this same one-row-per-couple-per-day mechanism rather than
    inventing a second one."""
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

    content = pick_content_for_couple(couple, activity_type=activity_type, spicy_unlocked_flag=spicy_unlocked_flag)
    if content is None:
        return None

    activity = Activity(couple_id=couple.id, content_id=content.id, is_daily=True)
    db.session.add(activity)
    db.session.flush()  # need activity.id before creating the ActivityDailySelection row

    daily = ActivityDailySelection(couple_id=couple.id, date=today, content_id=content.id, activity_id=activity.id)
    db.session.add(daily)
    db.session.commit()
    return activity


def create_random_activity(user, couple, category=None, activity_type="classic_question", spicy_unlocked_flag=False, mode="unanswered"):
    """The "give me something to answer" entry point behind each game's
    own random-fetch screen (and, incidentally, classic_question's
    "Answer Question" quick action - fixed by the same change, since it
    goes through this same function).

    mode="unanswered" (default): any content this user personally hasn't
    submitted for yet, in their current cycle for this activity_type. If
    the couple already has a pending (unrevealed) Activity for the chosen
    content - e.g. the partner started it - that SAME Activity is reused
    (via get_or_create_activity_for_content) rather than a duplicate being
    created, so submitting completes it immediately. Returns None once
    every eligible question this cycle has been personally answered.

    mode="partner_pending": specifically an existing pending Activity the
    partner has already submitted to and this user hasn't - never a fresh
    pick. Returns None (deliberately, no fallback to "unanswered") if
    nothing is currently pending from the partner.
    """
    if mode == "partner_pending":
        return find_partner_pending_activity(couple, user, activity_type, spicy_unlocked_flag=spicy_unlocked_flag)

    content = pick_content_for_user(
        user, couple, activity_type=activity_type, category=category, spicy_unlocked_flag=spicy_unlocked_flag,
    )
    if content is None:
        return None
    return get_or_create_activity_for_content(couple, content, for_user=user)


def get_or_create_activity_for_content(couple, content, for_user=None):
    """Used when a couple deliberately picks a specific piece of content
    (Browse screen) rather than getting a random/daily one. Reuses an
    in-progress (not yet revealed) Activity for the same content instead
    of spawning duplicates if they re-open it - same behaviour as the
    legacy get_or_create_round_for_question.

    for_user (set only by create_random_activity) additionally requires
    that the reused Activity has no submission from that user yet. This
    matters once Play Again starts a second cycle: the content becomes
    eligible again, but the first cycle's Activity may still be sitting
    unrevealed with this user's own submission on it. Reusing that one
    would make the submit fail as a duplicate and leave the content
    permanently "unanswered this cycle" - an endless repeat of the same
    question. A fresh Activity is the right answer there, and the old
    one stays exactly as it was, still completable by the partner.

    Browse deliberately does NOT pass for_user: re-opening a question you
    already answered should show your existing waiting/reveal state, not
    silently start a second round of the same question."""
    query = couple.activities.filter_by(content_id=content.id, revealed_at=None)
    existing = query.order_by(Activity.created_at.desc()).all()
    for activity in existing:
        if for_user is not None and activity.submission_for(for_user.id) is not None:
            continue
        return activity
    activity = Activity(couple_id=couple.id, content_id=content.id, is_daily=False)
    db.session.add(activity)
    db.session.commit()
    return activity


def get_current_cycle(user, activity_type):
    """Which pass through activity_type's content bank `user` is
    currently on. No row in ActivityCycle means cycle 1 - there's no
    need to eagerly create one just to answer this question."""
    row = ActivityCycle.query.filter_by(user_id=user.id, activity_type=activity_type).first()
    return row.cycle if row else 1


def advance_cycle(user, activity_type):
    """Play Again: every question becomes eligible for `user` again,
    without touching a single existing ActivitySubmission - those stay
    stamped with the cycle they were actually answered in, so history and
    scoring for the finished cycle are untouched. Returns the new cycle
    number."""
    row = ActivityCycle.query.filter_by(user_id=user.id, activity_type=activity_type).first()
    if row is None:
        row = ActivityCycle(user_id=user.id, activity_type=activity_type, cycle=2)
        db.session.add(row)
    else:
        row.cycle += 1
    db.session.commit()
    return row.cycle


def bank_has_any_content(activity_type, category=None, spicy_unlocked_flag=False):
    """Whether activity_type/category has ANY eligible content at all,
    independent of any specific user's progress - lets a caller tell
    "you've answered everything" (bank_exhausted) apart from "this
    activity_type/category isn't configured" (no_content)."""
    query = ActivityContent.query.filter_by(activity_type=activity_type, active=True)
    if category:
        if category == "spicy" and not spicy_unlocked_flag:
            return False
        query = query.filter_by(category=category)
    elif not spicy_unlocked_flag:
        query = query.filter(
            db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy")
        )
    return db.session.query(query.exists()).scalar()


def pick_content_for_user(user, couple, activity_type="classic_question", category=None, spicy_unlocked_flag=False, exclude_created_by_user_id=None):
    """Per-user counterpart to pick_content_for_couple(), used by
    create_random_activity(). "Already answered" is scoped to
    (user, activity_type, current cycle) via ActivitySubmission.cycle -
    see get_current_cycle/advance_cycle above - rather than to whether any
    Activity row exists for the content at all. This is the actual fix:
    content the partner has already submitted for is still a perfectly
    valid pick for this user (get_or_create_activity_for_content will
    correctly complete their pending Activity instead of duplicating it),
    it just isn't excluded from the pool anymore for the wrong reason.

    Falling back to "everything" when the per-user pool is empty (the way
    pick_content_for_couple does) would silently start repeating content
    without the person ever being told - wrong for a bank with an actual
    "you've finished it" milestone. Returns None instead, so the caller
    can distinguish "finished this cycle" from "nothing configured" (see
    bank_has_any_content) and offer Play Again rather than a quiet repeat.
    """
    query = ActivityContent.query.filter_by(activity_type=activity_type, active=True)
    if category:
        if category == "spicy" and not spicy_unlocked_flag:
            return None
        query = query.filter_by(category=category)
    elif not spicy_unlocked_flag:
        query = query.filter(
            db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy")
        )

    candidates = query.all()
    if exclude_created_by_user_id is not None:
        candidates = [c for c in candidates if c.payload.get("created_by_user_id") != exclude_created_by_user_id]
    if not candidates:
        return None

    current_cycle = get_current_cycle(user, activity_type)
    candidate_ids = [c.id for c in candidates]
    answered_content_ids = {
        row[0]
        for row in db.session.query(Activity.content_id)
        .join(ActivitySubmission, ActivitySubmission.activity_id == Activity.id)
        .filter(
            ActivitySubmission.user_id == user.id,
            ActivitySubmission.cycle == current_cycle,
            Activity.content_id.in_(candidate_ids),
        )
    }
    pool = [c for c in candidates if c.id not in answered_content_ids]
    if not pool:
        return None

    last_activity = couple.activities.order_by(Activity.created_at.desc()).first()
    if last_activity and len(pool) > 1:
        pool = [c for c in pool if c.id != last_activity.content_id] or pool

    return random.choice(pool)


def find_partner_pending_activity(couple, user, activity_type, spicy_unlocked_flag=False):
    """Mode 2 of the Answer Coordination toggle: an existing, unrevealed
    Activity for this couple + activity_type where the partner has
    already submitted and `user` hasn't. Returns the SAME Activity (never
    a new one), so submitting to it completes that pending round right
    away instead of starting a fresh, unrelated one.

    With exactly two members per couple, "partner submitted and not yet
    revealed" already implies "I haven't submitted" (reveal fires the
    moment both submissions exist - see ActivityHandler.reveal), so no
    extra check for the current user's own submission is needed here."""
    partner = couple.other_member(user)
    if partner is None:
        return None

    candidates = (
        couple.activities.join(ActivityContent)
        .filter(
            Activity.revealed_at.is_(None),
            ActivityContent.activity_type == activity_type,
            ActivityContent.active.is_(True),
        )
        .all()
    )

    pending = [
        activity for activity in candidates
        if not (activity.content.category == "spicy" and not spicy_unlocked_flag)
        and activity.submission_for(partner.id) is not None
    ]
    if not pending:
        return None
    return random.choice(pending)
