"""
Would You Rather: the first genuinely new game built on the reusable
Activity architecture - and proof the architecture works as intended.
No new database tables were needed; this entire game is
ActivityContent.payload = {"option_a", "option_b", "emoji_a"?, "emoji_b"?}
and ActivitySubmission.payload = {"choice": "a"|"b"}.

Mechanic: both partners privately choose "a" or "b" (base ActivityHandler
already enforces one submission per user, and serialize_activity already
guarantees the partner's choice is invisible until both are in - nothing
game-specific was needed for either of those guarantees). Once both have
chosen, exact-match scoring decides the result: +1 each on a match, +0
each otherwise (Building Us spec: "a match is +1 each, no match +0").
"""

from app.services import scoring
from app.services.activities.base import ActivityHandler, ActivityValidationError


class WouldYouRatherActivity(ActivityHandler):
    activity_type = "would_you_rather"

    def validate_payload(self, activity, raw_payload):
        choice = raw_payload.get("choice")
        if choice not in ("a", "b"):
            raise ActivityValidationError("Please choose option A or B.")
        return {"choice": choice}

    def compute_result(self, activity):
        user_a, user_b = activity.couple.ordered_members()
        sub_a = activity.submission_for(user_a.id)
        sub_b = activity.submission_for(user_b.id)

        outcome = scoring.compute_score(
            "exact_match",
            value_a=sub_a.payload.get("choice"),
            value_b=sub_b.payload.get("choice"),
        )
        points = 1 if outcome["matched"] else 0
        return {
            "is_competitive": True,
            "outcome": outcome["outcome"],
            "points": {str(user_a.id): points, str(user_b.id): points},
            "payload": {},
        }
