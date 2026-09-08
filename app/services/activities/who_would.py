"""
Who Would...?: both partners privately pick "me" or "partner" in answer
to "Who would be more likely to ___?", with an optional explanation.
Deliberately NOT competitive - see compute_result. This is a discussion
game, not a quiz (same design stance as Emoji Story, for the same reason:
the Building Us doc explicitly frames this one as "focus more on
discussion and humour than competition," and never lists it among the
point-earning games).

The interesting bit is that "me" and "partner" are RELATIVE to whoever
submitted them - Tom's "me" and Sarah's "partner" can both point at Tom.
compute_result resolves each submission's relative choice into the
actual user_id being nominated, so the reveal can show real names (like
the brief's own example: "Tom: Sarah / Sarah: Sarah") and so "unanimous"
can be determined by comparing the two resolved ids rather than the raw
strings (which would incorrectly call "me"+"partner" a mismatch every
time, even when both partners are naming the same person).
"""

from app.services.activities.base import ActivityHandler, ActivityValidationError

MAX_EXPLANATION_LENGTH = 300


class WhoWouldActivity(ActivityHandler):
    activity_type = "who_would"

    def validate_payload(self, activity, raw_payload):
        choice = raw_payload.get("choice")
        if choice not in ("me", "partner"):
            raise ActivityValidationError("Choose who you think is more likely.")

        explanation = (raw_payload.get("explanation") or "").strip()
        if len(explanation) > MAX_EXPLANATION_LENGTH:
            raise ActivityValidationError("Keep your explanation under 300 characters.")

        return {"choice": choice, "explanation": explanation or None}

    def compute_result(self, activity):
        user_a, user_b = activity.couple.ordered_members()
        sub_a = activity.submission_for(user_a.id)
        sub_b = activity.submission_for(user_b.id)

        a_picked_id = user_a.id if sub_a.payload.get("choice") == "me" else user_b.id
        b_picked_id = user_b.id if sub_b.payload.get("choice") == "me" else user_a.id

        unanimous = a_picked_id == b_picked_id

        return {
            "is_competitive": False,
            "outcome": "unanimous" if unanimous else "split",
            "points": {},
            "payload": {
                "picks": {
                    str(user_a.id): {"chose_user_id": a_picked_id},
                    str(user_b.id): {"chose_user_id": b_picked_id},
                }
            },
        }
