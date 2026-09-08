"""
Access control + response serialization for the new Activity system - the
direct counterpart to services/privacy.py for the legacy Round/Answer
system. Same rule, same enforcement point:

    A partner's submission is never included in any response, in any form,
    until the current user has submitted their own to the same activity.

This is the ONLY function in the codebase allowed to turn an Activity +
its ActivitySubmissions into JSON. Every activity route goes through
serialize_activity() rather than building response dicts itself.
"""

from app.models import Activity


class ActivityAccessDenied(Exception):
    """Raised when an activity does not belong to the current user's
    couple. Routes map this to a plain 404 - identical to a nonexistent
    ID - so a cross-couple probe can't confirm another couple's data
    exists, same as the legacy get_owned_round()."""


def get_owned_activity(activity_id, user):
    activity = Activity.query.get(activity_id)
    if activity is None or activity.couple_id != user.couple_id:
        raise ActivityAccessDenied()
    return activity


def _submission_view(submission, owner):
    if submission is None:
        return None
    if submission.is_private and not owner:
        return {"is_private": True, "hidden": True}
    return {
        "id": submission.id,
        "payload": submission.payload,
        "is_private": submission.is_private,
        "created_at": submission.created_at.isoformat() + "Z",
    }


def serialize_activity(activity, viewer):
    from app.services.activities import get_handler  # local import: avoids a
    # module-load-order cycle (activities/* never imports this module, but
    # importing it at top-level here would run activities/__init__.py -
    # and therefore every handler module - before app/models is fully
    # configured in some start-up orders. Safer to import where it's used.

    handler = get_handler(activity.content.activity_type)

    partner = activity.couple.other_member(viewer)
    my_submission = activity.submission_for(viewer.id)
    partner_submission = activity.submission_for(partner.id) if partner else None

    content_dict = activity.content.to_dict()
    # Most games have nothing to hide in their content (multiple-choice
    # options aren't secret) - but some (Emoji Story's intended
    # explanation) embed a secret in the CONTENT itself, not in a
    # submission. redact_content_payload defaults to a no-op for every
    # game that doesn't override it, so this changes nothing for existing
    # activity types.
    content_dict["payload"] = handler.redact_content_payload(
        activity.content, activity, viewer, activity.is_revealed
    )

    payload = {
        "activity_id": activity.id,
        "activity_type": activity.content.activity_type,
        "content": content_dict,
        "is_daily": activity.is_daily,
        "created_at": activity.created_at.isoformat() + "Z",
        "my_submitted": my_submission is not None,
        "partner_submitted": partner_submission is not None,
        "revealed": activity.is_revealed,
    }

    if my_submission is not None:
        payload["my_submission"] = _submission_view(my_submission, owner=True)

    if not activity.is_revealed:
        # Do not add a "partner_submission" key at all pre-reveal - the
        # response stops here. This mirrors serialize_round() exactly.
        return payload

    payload["partner_submission"] = _submission_view(partner_submission, owner=False)

    if activity.result is not None:
        payload["result"] = {
            "is_competitive": activity.result.is_competitive,
            "outcome": activity.result.outcome,
            "points": activity.result.points,
            "payload": activity.result.payload,
        }

    return payload
