"""
Everything that decides what a request is *allowed to see*.

This is the single most important module in the app. The rule enforced
throughout is:

    A partner's answer is never included in any API response, in any form
    (not even length, first letter, or an existence flag beyond a plain
    boolean), until the current user has submitted their own answer to the
    same round.

Every route that touches a Round or Answer goes through the helpers here
rather than querying/serialising models directly, so this rule only has to
be gotten right in one place.
"""

from app.models import Comment, Round


class AccessDenied(Exception):
    """Raised when a round/answer does not belong to the current user's
    couple. Routes catch this and return a 404 (not a 403) so we never
    confirm or deny the existence of another couple's data."""


def get_owned_round(round_id, user):
    """Fetch a Round, but only if it belongs to the current user's couple."""
    round_ = Round.query.get(round_id)
    if round_ is None or round_.couple_id != user.couple_id:
        raise AccessDenied()
    return round_


def get_owned_answer(answer_id, user):
    """Fetch an Answer, but only if it belongs to a round in the current
    user's couple AND that round has been revealed. Reactions/comments only
    make sense once both sides can actually see the answer."""
    from app.models import Answer

    answer = Answer.query.get(answer_id)
    if answer is None or answer.round.couple_id != user.couple_id:
        raise AccessDenied()
    if not answer.round.is_revealed:
        raise AccessDenied()
    return answer


def spicy_unlocked(couple):
    members = couple.ordered_members()
    return len(members) == 2 and all(m.spicy_opt_in for m in members)


def _answer_view(answer, owner):
    """Render one side of a round's answer, respecting the private flag."""
    if answer is None:
        return None
    if answer.is_private and not owner:
        return {"is_private": True, "hidden": True}
    return {
        "id": answer.id,
        "text": answer.answer_text,
        "option": answer.answer_option,
        "is_private": answer.is_private,
        "created_at": answer.created_at.isoformat() + "Z",
    }


def serialize_round(round_, viewer):
    """The one function that turns a Round into JSON for `viewer`.

    Pre-reveal, a partner's answer object is never touched at all - it is
    not queried into the response, not even in masked form - beyond the
    plain boolean `partner_answered`.
    """
    question = round_.question
    partner = round_.couple.other_member(viewer)

    my_answer = round_.answer_for(viewer.id)
    partner_answer = round_.answer_for(partner.id) if partner else None

    payload = {
        "round_id": round_.id,
        "question": question.to_dict(),
        "is_daily": round_.is_daily,
        "created_at": round_.created_at.isoformat() + "Z",
        "my_answered": my_answer is not None,
        "partner_answered": partner_answer is not None,
        "revealed": bool(round_.is_revealed),
    }

    if my_answer is not None:
        payload["my_answer"] = _answer_view(my_answer, owner=True)

    if not round_.is_revealed:
        # Do not add a "partner_answer" key at all pre-reveal.
        return payload

    payload["partner_answer"] = _answer_view(partner_answer, owner=False)

    if question.question_type == "prediction" and my_answer and partner_answer:
        payload["prediction"] = {
            "my_prediction_of_partner": my_answer.predicted_option,
            "partner_actual": partner_answer.answer_option,
            "i_guessed_correctly": (
                my_answer.predicted_option is not None
                and my_answer.predicted_option == partner_answer.answer_option
            ),
            "partner_prediction_of_me": partner_answer.predicted_option,
            "my_actual": my_answer.answer_option,
            "partner_guessed_correctly": (
                partner_answer.predicted_option is not None
                and partner_answer.predicted_option == my_answer.answer_option
            ),
        }

    payload["reactions"] = {
        "on_my_answer": [r.to_dict() for r in my_answer.reactions] if my_answer else [],
        "on_partner_answer": [r.to_dict() for r in partner_answer.reactions] if partner_answer else [],
    }
    payload["comments"] = [
        c.to_dict() for c in round_.comments.order_by(Comment.created_at.asc()).all()
    ]
    return payload
