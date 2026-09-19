"""
Challenges business logic. See app/models/challenge.py for why this
doesn't reuse the Activity/ActivityHandler machinery - no privacy
dimension, no submit-then-reveal shape, so it gets its own small service
instead of a forced-fit handler.
"""

import random
from datetime import datetime

from app.extensions import db
from app.models import ActivityContent, CoupleChallenge, CoupleChallengeCycle
from app.models.challenge import CHALLENGE_CATEGORIES, SPICY_GATED_CATEGORIES


class ChallengeError(Exception):
    """A well-formed but invalid request. Routes map this to 400."""


class ChallengeAccessDenied(Exception):
    """Challenge doesn't belong to the current user's couple. Routes map
    this to a plain 404, same convention as every other *AccessDenied."""


class SpicyLockedChallenge(Exception):
    """Spicy challenge content was requested/accepted/skipped while the
    couple's Spicy mode is locked. A distinct exception (not
    ChallengeError) so routes can map this to 403 spicy_locked - same
    status every other spicy-gated endpoint in the app uses - rather than
    the generic 400 used for ordinary validation problems."""


class ChallengeCategoryExhausted(Exception):
    """Every active challenge in the requested pool has already been
    accepted, completed, or skipped in the couple's current cycle for
    its category. Distinct from pick_challenge_for_couple returning None
    (which means the pool has no content at all) so routes/frontend can
    offer a Replay action specifically, rather than a generic "nothing
    here" message."""


def requires_spicy_unlock(category):
    """True if this category is gated behind the couple's dual Spicy
    opt-in - currently "spicy" itself and "longdistance" (equally
    explicit, just usable while apart). Centralised here so every
    gating check - accept, skip, list, pick, status - stays in sync if
    another gated category is ever added."""
    return category in SPICY_GATED_CATEGORIES


def get_owned_challenge(challenge_id, user):
    challenge = CoupleChallenge.query.get(challenge_id)
    if challenge is None or challenge.couple_id != user.couple_id:
        raise ChallengeAccessDenied()
    return challenge


def is_hidden_spicy_challenge(challenge, spicy_unlocked_flag):
    """True if this challenge's content is in a Spicy-gated category
    (Spicy or Long Distance) and the couple currently has Spicy locked -
    same policy as everywhere else in the app: treat it as if it doesn't
    exist, even via a challenge_id the user already has (a private
    item's status changing is itself a signal, so mutation needs the
    same protection as reads)."""
    return requires_spicy_unlock(challenge.content.category) and not spicy_unlocked_flag


def current_cycle_for_category(couple, category):
    """The couple's current replay cycle for this category. A missing
    CoupleChallengeCycle row means cycle 1 - never replayed - see the
    model docstring for why no row is created just to read this."""
    row = CoupleChallengeCycle.query.filter_by(couple_id=couple.id, category=category).first()
    return row.current_cycle if row else 1


def _engaged_content_ids_for_pool(couple):
    """Content ids that count as 'already engaged' against the couple's
    *current* cycle in each item's own category - i.e. accepted,
    completed, or skipped since the last time that category was last
    replayed. Rows from before a replay don't count against the fresh
    pool; they're left in the database purely as history."""
    cycle_cache = {}
    engaged = set()
    for cc in couple.challenges.all():
        category = cc.content.category
        if category not in cycle_cache:
            cycle_cache[category] = current_cycle_for_category(couple, category)
        if cc.cycle == cycle_cache[category]:
            engaged.add(cc.content_id)
    return engaged


def pick_challenge_for_couple(couple, category=None, spicy_unlocked_flag=False):
    """A stateless candidate suggestion - nothing is written to the
    database by picking. Excludes challenges this couple has already
    accepted, completed, or skipped in the current cycle for their
    category (see _engaged_content_ids_for_pool), until that pool is
    exhausted - at which point this raises ChallengeCategoryExhausted
    rather than silently repeating content, so the caller can offer a
    Replay action instead.

    Explicit category="spicy" while locked is rejected by the route
    before this is even called (403, same as every other spicy-gated
    endpoint). This function's job is the *implicit* case: an
    unfiltered "any category" pick must never surface Spicy content
    while locked either - and, separately, never surfaces it even once
    unlocked, since Spicy is deliberately excluded from the unfiltered
    "All" pool regardless of lock state (see the "spicy tab only"
    behaviour this was written for)."""
    if category is not None and category not in CHALLENGE_CATEGORIES:
        raise ChallengeError("Unknown category.")

    query = ActivityContent.query.filter_by(activity_type="challenge", active=True)
    if category:
        query = query.filter_by(category=category)
    else:
        # "All": every Spicy-gated category excluded unconditionally, even
        # once unlocked - only an explicit gated-category pick (its own
        # dedicated tab) ever surfaces it.
        query = query.filter(
            db.or_(
                ActivityContent.category.is_(None),
                ActivityContent.category.notin_(SPICY_GATED_CATEGORIES),
            )
        )
    candidates = query.all()
    if not candidates:
        return None

    engaged_ids = _engaged_content_ids_for_pool(couple)
    pool = [c for c in candidates if c.id not in engaged_ids]
    if not pool:
        raise ChallengeCategoryExhausted()

    return random.choice(pool)


def is_category_exhausted(couple, category, spicy_unlocked_flag=False):
    """True if every active challenge in this category has already been
    accepted, completed, or skipped in the couple's current cycle. False
    (not exhausted) if the category simply has no content at all - that's
    a different situation, not one Replay solves."""
    candidates = ActivityContent.query.filter_by(
        activity_type="challenge", active=True, category=category
    ).all()
    if not candidates:
        return False
    engaged_ids = _engaged_content_ids_for_pool(couple)
    return all(c.id in engaged_ids for c in candidates)


def replay_category(couple, category):
    """Start a fresh cycle for this category: every challenge in it
    becomes eligible for suggestion again. Nothing is deleted - every
    prior accepted/completed/skipped row stays exactly as it was, as
    permanent history; it just stops counting against the new cycle's
    pool (see _engaged_content_ids_for_pool)."""
    if category not in CHALLENGE_CATEGORIES:
        raise ChallengeError("Unknown category.")

    cycle_row = CoupleChallengeCycle.query.filter_by(couple_id=couple.id, category=category).first()
    if cycle_row is None:
        cycle_row = CoupleChallengeCycle(couple_id=couple.id, category=category, current_cycle=2)
        db.session.add(cycle_row)
    else:
        cycle_row.current_cycle += 1
    db.session.commit()
    return cycle_row.current_cycle


def accept_challenge(couple, content_id, spicy_unlocked_flag=False):
    """Idempotent within the current cycle: accepting the same challenge
    twice (e.g. a double-tap, or a race between partners both looking at
    the same suggestion) returns the existing row rather than erroring or
    duplicating. After a replay, the same content_id can be accepted
    again - it gets a new row stamped with the new cycle, tracked
    separately from its history in earlier cycles.

    Content is looked up (and the Spicy gate checked) before the
    idempotent-existing-row shortcut, not after - otherwise re-accepting
    an already-accepted Spicy challenge while locked would leak that it
    exists via the returned row, bypassing the gate entirely."""
    content = ActivityContent.query.get(content_id)
    if content is None or content.activity_type != "challenge" or not content.active:
        raise ChallengeError("That challenge isn't available.")
    if requires_spicy_unlock(content.category) and not spicy_unlocked_flag:
        raise SpicyLockedChallenge()

    cycle = current_cycle_for_category(couple, content.category)

    existing = CoupleChallenge.query.filter_by(
        couple_id=couple.id, content_id=content_id, cycle=cycle
    ).first()
    if existing is not None:
        return existing

    challenge = CoupleChallenge(
        couple_id=couple.id,
        content_id=content.id,
        cycle=cycle,
        status="accepted",
        requires_both=bool(content.payload.get("requires_both")),
    )
    challenge.completed_by = []
    db.session.add(challenge)
    db.session.commit()
    return challenge


def skip_challenge(couple, content_id, spicy_unlocked_flag=False):
    """Records a skip so this challenge won't be suggested again this
    cycle. Idempotent the same way accept_challenge is: skipping twice,
    or skipping something already accepted/completed this cycle, just
    returns the existing row unchanged rather than overwriting its
    status - a skip should never quietly undo a completion."""
    content = ActivityContent.query.get(content_id)
    if content is None or content.activity_type != "challenge" or not content.active:
        raise ChallengeError("That challenge isn't available.")
    if requires_spicy_unlock(content.category) and not spicy_unlocked_flag:
        raise SpicyLockedChallenge()

    cycle = current_cycle_for_category(couple, content.category)

    existing = CoupleChallenge.query.filter_by(
        couple_id=couple.id, content_id=content_id, cycle=cycle
    ).first()
    if existing is not None:
        return existing

    skipped = CoupleChallenge(
        couple_id=couple.id,
        content_id=content.id,
        cycle=cycle,
        status="skipped",
        requires_both=bool(content.payload.get("requires_both")),
    )
    skipped.completed_by = []
    db.session.add(skipped)
    db.session.commit()
    return skipped


def complete_challenge(challenge, user):
    if challenge.status == "completed":
        raise ChallengeError("This challenge is already marked complete.")
    if challenge.status == "skipped":
        raise ChallengeError("This challenge was skipped, not accepted.")

    completed_by = set(challenge.completed_by)
    if user.id in completed_by:
        raise ChallengeError("You've already confirmed your part.")
    completed_by.add(user.id)
    challenge.completed_by = list(completed_by)

    if not challenge.requires_both or len(completed_by) >= 2:
        challenge.status = "completed"
        challenge.completed_at = datetime.utcnow()

    db.session.commit()
    return challenge


def list_challenges(couple, status=None, category=None, spicy_unlocked_flag=False):
    """The couple's own accepted/skipped/completed challenges, across
    every cycle - this is a full history view, not scoped to the current
    cycle (use is_category_exhausted / current_cycle_for_category for
    "what's the state of my current pool" instead).

    category=None is the "All" tab. Spicy is deliberately excluded from
    it unconditionally - unlike every other Spicy content type in this
    app (Questions, Activities, Rounds), where Spicy behaves as a normal
    category and appears in "All" once unlocked, Challenges never
    surfaces Spicy outside the dedicated Spicy tab. That's a deliberate
    divergence from the rest of the app's pattern, not an oversight.

    category="spicy" is the dedicated Spicy tab: requires unlocked, same
    403 pattern as every other spicy-gated endpoint. Any other specific
    category filters normally - Spicy is irrelevant there.
    """
    query = couple.challenges
    if status:
        query = query.filter_by(status=status)

    if category:
        if requires_spicy_unlock(category) and not spicy_unlocked_flag:
            raise SpicyLockedChallenge()
        query = query.join(ActivityContent).filter(ActivityContent.category == category)
    else:
        query = query.join(ActivityContent).filter(
            db.or_(
                ActivityContent.category.is_(None),
                ActivityContent.category.notin_(SPICY_GATED_CATEGORIES),
            )
        )

    return query.order_by(CoupleChallenge.accepted_at.desc()).all()


def serialize_challenge(challenge, viewer):
    return {
        "id": challenge.id,
        "content_id": challenge.content_id,
        "prompt": challenge.content.prompt,
        "category": challenge.content.category,
        "status": challenge.status,
        "cycle": challenge.cycle,
        "requires_both": challenge.requires_both,
        "completed_by": challenge.completed_by,
        "i_have_completed": viewer.id in challenge.completed_by,
        "accepted_at": challenge.accepted_at.isoformat() + "Z",
        "completed_at": challenge.completed_at.isoformat() + "Z" if challenge.completed_at else None,
    }
