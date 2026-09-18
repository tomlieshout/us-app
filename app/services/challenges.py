"""
Challenges business logic. See app/models/challenge.py for why this
doesn't reuse the Activity/ActivityHandler machinery - no privacy
dimension, no submit-then-reveal shape, so it gets its own small service
instead of a forced-fit handler.
"""

import random
from datetime import datetime

from app.extensions import db
from app.models import ActivityContent, CoupleChallenge
from app.models.challenge import CHALLENGE_CATEGORIES


class ChallengeError(Exception):
    """A well-formed but invalid request. Routes map this to 400."""


class ChallengeAccessDenied(Exception):
    """Challenge doesn't belong to the current user's couple. Routes map
    this to a plain 404, same convention as every other *AccessDenied."""


class SpicyLockedChallenge(Exception):
    """Spicy challenge content was requested/accepted while the couple's
    Spicy mode is locked. A distinct exception (not ChallengeError) so
    routes can map this to 403 spicy_locked - same status every other
    spicy-gated endpoint in the app uses - rather than the generic 400
    used for ordinary validation problems."""


def get_owned_challenge(challenge_id, user):
    challenge = CoupleChallenge.query.get(challenge_id)
    if challenge is None or challenge.couple_id != user.couple_id:
        raise ChallengeAccessDenied()
    return challenge


def is_hidden_spicy_challenge(challenge, spicy_unlocked_flag):
    """True if this challenge's content is Spicy and the couple currently
    has Spicy locked - same policy as everywhere else in the app: treat
    it as if it doesn't exist, even via a challenge_id the user already
    has (a private item's status changing is itself a signal, so
    mutation needs the same protection as reads)."""
    return challenge.content.category == "spicy" and not spicy_unlocked_flag


def pick_challenge_for_couple(couple, category=None, spicy_unlocked_flag=False):
    """A stateless candidate suggestion - nothing is written to the
    database. Excludes challenges this couple has already accepted
    (whether completed or still pending), never repeating a challenge
    they've already engaged with, until the pool is exhausted.

    Explicit category="spicy" while locked is rejected by the route
    before this is even called (403, same as every other spicy-gated
    endpoint). This function's job is the *implicit* case: an
    unfiltered "any category" pick must never surface Spicy content
    while locked either."""
    if category is not None and category not in CHALLENGE_CATEGORIES:
        raise ChallengeError("Unknown category.")

    query = ActivityContent.query.filter_by(activity_type="challenge", active=True)
    if category:
        query = query.filter_by(category=category)
    elif not spicy_unlocked_flag:
        query = query.filter(db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy"))
    candidates = query.all()
    if not candidates:
        return None

    already_engaged_ids = {cc.content_id for cc in couple.challenges.all()}
    pool = [c for c in candidates if c.id not in already_engaged_ids]
    if not pool:
        pool = candidates  # exhausted the couple's fresh pool - allow repeats

    return random.choice(pool)


def accept_challenge(couple, content_id, spicy_unlocked_flag=False):
    """Idempotent: accepting the same challenge twice (e.g. a double-tap,
    or a race between partners both looking at the same suggestion)
    returns the existing row rather than erroring or duplicating.

    Content is looked up (and the Spicy gate checked) before the
    idempotent-existing-row shortcut, not after - otherwise re-accepting
    an already-accepted Spicy challenge while locked would leak that it
    exists via the returned row, bypassing the gate entirely."""
    content = ActivityContent.query.get(content_id)
    if content is None or content.activity_type != "challenge" or not content.active:
        raise ChallengeError("That challenge isn't available.")
    if content.category == "spicy" and not spicy_unlocked_flag:
        raise SpicyLockedChallenge()

    existing = CoupleChallenge.query.filter_by(couple_id=couple.id, content_id=content_id).first()
    if existing is not None:
        return existing

    challenge = CoupleChallenge(
        couple_id=couple.id,
        content_id=content.id,
        status="accepted",
        requires_both=bool(content.payload.get("requires_both")),
    )
    challenge.completed_by = []
    db.session.add(challenge)
    db.session.commit()
    return challenge


def complete_challenge(challenge, user):
    if challenge.status == "completed":
        raise ChallengeError("This challenge is already marked complete.")

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
    """The couple's own accepted/in-progress/completed challenges.

    category=None is the "All" tab. Spicy is deliberately excluded from
    it unconditionally - unlike every other Spicy content type in this
    app (Questions, Activities, Rounds), where Spicy behaves as a normal
    category and appears in "All" once unlocked, Challenges never
    surfaces Spicy outside the dedicated Spicy tab. That's a deliberate
    divergence from the rest of the app's pattern, not an oversight -
    see the "spicy tab only" requirement this was written for.

    category="spicy" is the dedicated Spicy tab: requires unlocked,
    same 403 pattern as every other spicy-gated endpoint. Any other
    specific category filters normally - Spicy is irrelevant there.
    """
    query = couple.challenges
    if status:
        query = query.filter_by(status=status)

    if category:
        if category == "spicy" and not spicy_unlocked_flag:
            raise SpicyLockedChallenge()
        query = query.join(ActivityContent).filter(ActivityContent.category == category)
    else:
        query = query.join(ActivityContent).filter(
            db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy")
        )

    return query.order_by(CoupleChallenge.accepted_at.desc()).all()


def serialize_challenge(challenge, viewer):
    return {
        "id": challenge.id,
        "content_id": challenge.content_id,
        "prompt": challenge.content.prompt,
        "category": challenge.content.category,
        "status": challenge.status,
        "requires_both": challenge.requires_both,
        "completed_by": challenge.completed_by,
        "i_have_completed": viewer.id in challenge.completed_by,
        "accepted_at": challenge.accepted_at.isoformat() + "Z",
        "completed_at": challenge.completed_at.isoformat() + "Z" if challenge.completed_at else None,
    }
