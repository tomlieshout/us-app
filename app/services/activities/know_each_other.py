"""
Know Each Other: the second new game on the reusable Activity
architecture, and the first that needed no new scoring primitives at all -
both rules it needs (multiple-choice prediction correctness, and rating
difference) already existed in app/services/scoring.py, written for
classic_question's legacy "prediction" and "rating" subtypes. This handler
just composes them for a two-field submission instead of inventing
anything new - exactly the "game-specific scoring by composition" the
scoring module was designed to support.

Mechanic: each partner submits BOTH their own real answer AND their
prediction of the other's answer, in one submission (no strict "who goes
first" - the app is asynchronous, see build brief principle #1). Once
both have submitted, both directions are scored independently: did A
correctly guess B, and separately did B correctly guess A. Content is
either multiple_choice (options list, no "correct" answer - correctness
is about matching the partner) or rating (a 1-10 scale, options are the
numeric strings "1".."10", same convention as classic_question's rating
type).
"""

from app.services import scoring
from app.services.activities.base import ActivityHandler, ActivityValidationError


class KnowEachOtherActivity(ActivityHandler):
    activity_type = "know_each_other"

    def validate_payload(self, activity, raw_payload):
        options = activity.content.payload.get("options") or []
        answer = raw_payload.get("answer_option")
        predicted = raw_payload.get("predicted_option")

        if answer not in options:
            raise ActivityValidationError("Please choose your real answer.")
        if predicted not in options:
            raise ActivityValidationError("Please choose what you think your partner will say.")

        return {"answer_option": answer, "predicted_option": predicted}

    def compute_result(self, activity):
        qtype = activity.content.payload.get("question_type")
        user_a, user_b = activity.couple.ordered_members()
        sub_a = activity.submission_for(user_a.id)
        sub_b = activity.submission_for(user_b.id)

        a_actual = sub_a.payload.get("answer_option")
        b_actual = sub_b.payload.get("answer_option")
        a_predicted = sub_a.payload.get("predicted_option")  # A's guess about B
        b_predicted = sub_b.payload.get("predicted_option")  # B's guess about A

        if qtype == "multiple_choice":
            a_result = scoring.compute_score("prediction", predicted=a_predicted, actual=b_actual)
            b_result = scoring.compute_score("prediction", predicted=b_predicted, actual=a_actual)
            a_points = 1 if a_result["correct"] else 0
            b_points = 1 if b_result["correct"] else 0
            a_label = "correct" if a_result["correct"] else "incorrect"
            b_label = "correct" if b_result["correct"] else "incorrect"
        elif qtype == "rating":
            a_result = scoring.compute_score("rating_difference", value_a=a_predicted, value_b=b_actual)
            b_result = scoring.compute_score("rating_difference", value_a=b_predicted, value_b=a_actual)
            a_points = a_result["points_each"]
            b_points = b_result["points_each"]
            a_label = a_result["outcome"]
            b_label = b_result["outcome"]
        else:
            raise ActivityValidationError(f"Unsupported know_each_other question_type: {qtype!r}")

        if a_points > 0 and b_points > 0:
            outcome = "both_scored"
        elif a_points == 0 and b_points == 0:
            outcome = "neither_scored"
        else:
            outcome = "one_scored"

        return {
            "is_competitive": True,
            "outcome": outcome,
            "points": {str(user_a.id): a_points, str(user_b.id): b_points},
            "payload": {
                "predictions": {
                    str(user_a.id): {"predicted": a_predicted, "partner_actual": b_actual, "outcome": a_label, "points": a_points},
                    str(user_b.id): {"predicted": b_predicted, "partner_actual": a_actual, "outcome": b_label, "points": b_points},
                }
            },
        }
