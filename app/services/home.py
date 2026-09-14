"""
Home dashboard aggregation - the app's "daily starting point" view.

Pure aggregation: reads from systems that already exist (Activity/
ActivityContent, Appreciation, CoupleChallenge, Plan, Memory,
compute_competitive_stats) and reuses their existing selection/privacy/
gating logic instead of reimplementing any of it. No new database table -
"today's pick" already has a home in ActivityDailySelection (couple+date,
type-agnostic by schema), and the competitive numbers are already
Spicy-safe (see app/services/stats.py).

Spicy policy, consistent with everywhere else in the app:
  - Today's Activity CAN land on Spicy content once unlocked, same as
    every other daily/random picker (see pick_content_for_couple) -
    excluded while locked, normal once both partners opt in.
  - Recent Activity and Current Champion NEVER include anything Spicy,
    on any lock state - matching Stats' existing carve-out and the
    explicit "never show sensitive spicy information" requirement for
    this feed.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.extensions import db
from app.models import Activity, ActivityContent, Appreciation, CoupleChallenge, Memory, Plan
from app.services.activity_privacy import serialize_activity
from app.services.activity_questions import get_or_create_daily_activity
from app.services.appreciation import unseen_count
from app.services.questions import couple_local_today
from app.services.stats import compute_competitive_stats

# Today's Activity rotates through five lanes, one per day, the same for
# both partners - day-of-year, not random-per-request, matching the
# "shared daily thing" spirit of the existing question/round mechanic.
_LANES = ["question", "game", "appreciation", "challenge", "plan"]

# The "game" lane sub-rotates across these three Activity types. Emoji
# Story is deliberately excluded - it's a create/guess pair, not a single
# submit-then-reveal activity like the other three, so it doesn't fit the
# Waiting/Ready shape this lane needs. Still fully playable from the
# Games tab, just not part of Home's daily pin.
_GAME_TYPES = ["would_you_rather", "know_each_other", "who_would"]

_TYPE_LABELS = {
    "classic_question": "Question",
    "would_you_rather": "Would You Rather",
    "know_each_other": "Know Each Other",
    "who_would": "Who Would...?",
}


def get_home_data(couple, viewer, spicy_unlocked_flag):
    return {
        "today": _todays_activity(couple, viewer, spicy_unlocked_flag),
        "recent_activity": _recent_activity(couple, viewer),
        "champion": _champion(couple),
        "unseen_appreciation_count": unseen_count(viewer),
    }


# ------------------------------------------------------------- Today's Activity

def _todays_activity(couple, viewer, spicy_unlocked_flag):
    today = couple_local_today(couple)
    lane = _LANES[today.toordinal() % len(_LANES)]

    if lane == "question":
        result = _reveal_lane(couple, viewer, spicy_unlocked_flag, "classic_question")
        if result is not None:
            return result
    elif lane == "game":
        # Try every game type, starting with today's pick, before giving
        # up - a couple that's exhausted one type's pool (or, while
        # locked, has only Spicy content left in it) should still get a
        # game if ANY type has something playable, not nothing.
        start = today.toordinal() % len(_GAME_TYPES)
        ordered_types = _GAME_TYPES[start:] + _GAME_TYPES[:start]
        for game_type in ordered_types:
            result = _reveal_lane(couple, viewer, spicy_unlocked_flag, game_type)
            if result is not None:
                return result
    else:
        return _action_lane(couple, today, lane)

    # Every reveal-lane option came back empty (an exhausted or otherwise
    # empty content pool - shouldn't happen with the real seeded bank, but
    # action lanes never depend on content existing, so fall back to one
    # rather than ever returning nothing and leaving the frontend with a
    # null "today" to handle.
    return _action_lane(couple, today, "appreciation")


def _reveal_lane(couple, viewer, spicy_unlocked_flag, activity_type):
    activity = get_or_create_daily_activity(couple, spicy_unlocked_flag=spicy_unlocked_flag, activity_type=activity_type)
    if activity is None:
        return None
    return {
        "kind": "reveal",
        "lane": "question" if activity_type == "classic_question" else "game",
        "activity_type": activity_type,
        "label": _TYPE_LABELS.get(activity_type, activity_type),
        "activity": serialize_activity(activity, viewer),
    }


_ACTION_COPY = {
    "appreciation": {
        "emoji": "💌",
        "title": "Send an appreciation",
        "subtitle": "Let your partner know you're thinking of them today.",
        "done_subtitle": "You've sent an appreciation today",
    },
    "challenge": {
        "emoji": "🎲",
        "title": "Take on a challenge",
        "subtitle": "Accept a couple challenge and see it through together.",
        "done_subtitle": "You've completed a challenge today",
    },
    "plan": {
        "emoji": "📝",
        "title": "Add to your plans",
        "subtitle": "Got an idea for a date, trip, or something to try? Add it.",
        "done_subtitle": "You've added a plan today",
    },
}


def _action_lane(couple, today, lane):
    start = _local_midnight_utc(couple, today)

    if lane == "appreciation":
        done_today = (
            Appreciation.query.filter(Appreciation.couple_id == couple.id, Appreciation.created_at >= start).first()
            is not None
        )
    elif lane == "challenge":
        # Same Spicy exclusion as everywhere else - a Spicy challenge
        # completed today should not flip this lane to "done", the same
        # way it doesn't move Stats.
        done_today = (
            CoupleChallenge.query.join(ActivityContent, CoupleChallenge.content_id == ActivityContent.id)
            .filter(
                CoupleChallenge.couple_id == couple.id,
                CoupleChallenge.status == "completed",
                CoupleChallenge.completed_at >= start,
                db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy"),
            )
            .first()
            is not None
        )
    else:  # plan
        done_today = Plan.query.filter(Plan.couple_id == couple.id, Plan.created_at >= start).first() is not None

    return {"kind": "action", "lane": lane, "state": "done_today" if done_today else "todo", **_ACTION_COPY[lane]}


def _local_midnight_utc(couple, day):
    """`day` (a local date) as a naive UTC datetime, for comparing against
    created_at/completed_at columns - all naive UTC (datetime.utcnow)
    throughout this codebase."""
    try:
        tz = ZoneInfo(couple.timezone or "UTC")
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    local_midnight = datetime.combine(day, time.min, tzinfo=tz)
    return local_midnight.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


# ------------------------------------------------------------- Recent Activity

def _recent_activity(couple, viewer, limit=12):
    """Reverse-chronological merge across every system that produces a
    couple-visible event. Spicy is excluded from the Activity/Challenge
    sources below, always - never conditionally on lock state, matching
    Stats (see app/services/stats.py) and the explicit "never show
    sensitive spicy information" requirement for this feed.

    "Shared match" isn't a separate query here: every match_eligible
    question in the bank today is Spicy, so it's excluded by the same
    filter - this bucket is correctly empty right now, not broken. A
    future non-Spicy match-eligible category would need its own small
    query added here to actually surface.
    """
    items = []

    activities = (
        db.session.query(Activity, ActivityContent)
        .join(ActivityContent, Activity.content_id == ActivityContent.id)
        .filter(
            Activity.couple_id == couple.id,
            Activity.revealed_at.isnot(None),
            db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy"),
        )
        .order_by(Activity.revealed_at.desc())
        .limit(limit)
        .all()
    )
    for activity, content in activities:
        label = _TYPE_LABELS.get(content.activity_type, content.activity_type.replace("_", " ").title())
        verb = "answered" if content.activity_type == "classic_question" else "played"
        items.append(
            {
                "type": "game_completed",
                "timestamp": activity.revealed_at.isoformat(),
                "text": f"You both {verb} {label}",
            }
        )

    appreciations = (
        Appreciation.query.filter_by(couple_id=couple.id).order_by(Appreciation.created_at.desc()).limit(limit).all()
    )
    for a in appreciations:
        items.append(
            {
                "type": "appreciation_received",
                "timestamp": a.created_at.isoformat(),
                "text": f"{a.sender.name if a.sender else 'Your partner'} sent an appreciation",
            }
        )

    plans = Plan.query.filter_by(couple_id=couple.id).order_by(Plan.created_at.desc()).limit(limit).all()
    for p in plans:
        p_dict = p.to_dict(viewer=viewer)
        if p_dict.get("hidden"):
            text = f"{p_dict['added_by_name']} added a private plan" if p_dict.get("added_by_name") else "A private plan was added"
        else:
            text = f'Added "{p_dict["title"]}" to Plans'
        items.append({"type": "plan_added", "timestamp": p.created_at.isoformat(), "text": text})

    completed_challenges = (
        CoupleChallenge.query.join(ActivityContent, CoupleChallenge.content_id == ActivityContent.id)
        .filter(
            CoupleChallenge.couple_id == couple.id,
            CoupleChallenge.status == "completed",
            db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy"),
        )
        .order_by(CoupleChallenge.completed_at.desc())
        .limit(limit)
        .all()
    )
    for c in completed_challenges:
        items.append(
            {
                "type": "challenge_completed",
                "timestamp": c.completed_at.isoformat(),
                "text": f'Completed the challenge "{c.content.prompt}"',
            }
        )

    memories = Memory.query.filter_by(couple_id=couple.id).order_by(Memory.created_at.desc()).limit(limit).all()
    for m in memories:
        items.append({"type": "memory_created", "timestamp": m.created_at.isoformat(), "text": f'Added a memory: "{m.title}"'})

    items.sort(key=lambda i: i["timestamp"], reverse=True)
    return items[:limit]


# ------------------------------------------------------------- Current Champion

def _champion(couple):
    """Same shape compute_competitive_stats() already returns for
    points/leader/is_draw/games_played (it already excludes Spicy - see
    app/services/stats.py) - deliberately NOT trimmed down further, so
    the frontend can reuse stats.js's existing renderChampionBanner()
    unchanged rather than duplicating its margin-computation logic here
    as well."""
    stats = compute_competitive_stats(couple)
    return {
        "points": stats["points"],
        "leader": stats["leader"],
        "is_draw": stats["is_draw"],
        "games_played": stats["games_played"],
    }
