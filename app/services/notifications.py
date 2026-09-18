"""
Notification creation + retrieval. See app/models/notification.py for why
this is its own small table. Called directly from the routes that already
own each triggering event (activities, appreciation, plans) rather than
from base.py/scoring.py - see that file's docstring for the reasoning
(keeps scripts/backfill_activity_results.py from flooding the feed).

Every creator here follows the same two guarantees the rest of the app
already established elsewhere:
  - Spicy content is excluded entirely - game_answered/game_ready never
    fire for it, same reasoning as Stats/Recent Activity/Home.
  - A private Plan never generates a notification to the partner - same
    reasoning as routes/plans.py's _can_mutate/_matched_plan_ids: a
    private item's existence isn't something the partner should learn
    through a side channel, including this one.
"""

from app.extensions import db
from app.models import Notification

DEFAULT_LIST_LIMIT = 30


def _create(couple_id, recipient_user_id, type_, text, activity_type=None):
    from app.models.notification import MAX_TEXT_LENGTH

    text = text.strip()
    if len(text) > MAX_TEXT_LENGTH:
        text = text[: MAX_TEXT_LENGTH - 1].rstrip() + "…"

    notification = Notification(
        couple_id=couple_id,
        recipient_user_id=recipient_user_id,
        type=type_,
        text=text,
        activity_type=activity_type,
    )
    db.session.add(notification)
    return notification


def notify_game_answered(activity, waiting_on_user):
    """Call after a submit() that did NOT complete the activity - nudges
    whichever partner hasn't gone yet that the other one has."""
    if activity.content.category == "spicy":
        return
    submitter = activity.couple.other_member(waiting_on_user)
    name = submitter.name if submitter else "Your partner"
    _create(
        activity.couple_id,
        waiting_on_user.id,
        "game_answered",
        f"❤️ {name} answered — your turn!",
        activity_type=activity.content.activity_type,
    )
    db.session.commit()


def notify_game_ready(activity):
    """Call after a submit() that DID complete the activity - both
    partners can now reveal."""
    if activity.content.category == "spicy":
        return
    for member in activity.couple.ordered_members():
        _create(
            activity.couple_id,
            member.id,
            "game_ready",
            "💌 Your answers are ready to reveal!",
            activity_type=activity.content.activity_type,
        )
    db.session.commit()


def notify_appreciation_received(appreciation):
    _create(
        appreciation.couple_id,
        appreciation.recipient_user_id,
        "appreciation_received",
        f"💌 {appreciation.sender.name} sent you an appreciation",
    )
    db.session.commit()


def notify_plan_added(plan):
    if plan.is_private:
        return
    partner = plan.couple.other_member(plan.added_by)
    if partner is None:
        return
    _create(
        plan.couple_id,
        partner.id,
        "plan_added",
        f"📝 {plan.added_by.name} added a plan: {plan.title}",
    )
    db.session.commit()


def notify_shared_match(couple, title):
    """Both partners learn about a freshly-discovered match at the same
    time - matching is inherently mutual, there's no "waiting on partner"
    framing that would make sense here the way there is for games."""
    for member in couple.ordered_members():
        _create(couple.id, member.id, "shared_match", f"🔥 You both want to: {title}!")
    db.session.commit()


def notify_new_champion(couple, leader_name):
    for member in couple.ordered_members():
        _create(couple.id, member.id, "new_champion", f"👑 {leader_name} is now the champion!")
    db.session.commit()


def list_notifications(user, limit=DEFAULT_LIST_LIMIT):
    return (
        Notification.query.filter_by(recipient_user_id=user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def unseen_count(user):
    return Notification.query.filter_by(recipient_user_id=user.id, is_seen=False).count()


def mark_all_seen(user):
    Notification.query.filter_by(recipient_user_id=user.id, is_seen=False).update({"is_seen": True})
    db.session.commit()
