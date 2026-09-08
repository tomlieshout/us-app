"""
The first activity_type implementation: "classic_question" - the same
content that used to only exist as legacy Question/Answer rows, now
playable through the new Activity engine (see
scripts/migrate_questions_to_activities.py for how the content got here).

One activity_type, but it still has to handle every original question_type
(free_text / multiple_choice / rating / prediction / structured_scale),
since that distinction was preserved inside ActivityContent.payload rather
than split into separate new activity_types - see app/models/activity.py.

Scoring policy for this handler (server-side only, via app.services.scoring):
    free_text          -> not competitive, no score (same as the legacy app)
    structured_scale    -> not competitive, no score (these feed Spicy's
                           separate "find your matches" feature, not a
                           competitive score - keeping that boundary here too)
    multiple_choice     -> exact_match: +1 each on a match, +0 each otherwise
    rating               -> rating_difference: +2 exact / +1 within one / +0
    prediction            -> prediction: +1 per correct guess, scored once per
                           direction (each partner's own prediction of the
                           other is judged independently)
"""

from app.services import scoring
from app.services.activities.base import ActivityHandler, ActivityValidationError

MAX_TEXT_LENGTH = 2000

NON_COMPETITIVE_TYPES = {"free_text", "structured_scale"}


class ClassicQuestionActivity(ActivityHandler):
    activity_type = "classic_question"

    def validate_payload(self, activity, raw_payload):
        content_payload = activity.content.payload
        qtype = content_payload.get("question_type")
        options = content_payload.get("options") or []

        if qtype == "free_text":
            text = (raw_payload.get("answer_text") or "").strip()
            if not text:
                raise ActivityValidationError("Please write an answer.")
            if len(text) > MAX_TEXT_LENGTH:
                raise ActivityValidationError("That answer is too long.")
            return {"answer_text": text, "answer_option": None, "predicted_option": None}

        if qtype in ("multiple_choice", "rating", "structured_scale"):
            option = raw_payload.get("answer_option")
            if option not in options:
                raise ActivityValidationError("Please choose one of the given options.")
            return {"answer_text": None, "answer_option": option, "predicted_option": None}

        if qtype == "prediction":
            option = raw_payload.get("answer_option")
            predicted = raw_payload.get("predicted_option")
            if option not in options:
                raise ActivityValidationError("Please choose your real answer.")
            if predicted not in options:
                raise ActivityValidationError("Please choose what you think your partner will say.")
            return {"answer_text": None, "answer_option": option, "predicted_option": predicted}

        raise ActivityValidationError(f"Unsupported classic question_type: {qtype!r}")

    def compute_result(self, activity):
        qtype = activity.content.payload.get("question_type")
        user_a, user_b = activity.couple.ordered_members()
        sub_a = activity.submission_for(user_a.id)
        sub_b = activity.submission_for(user_b.id)

        if qtype in NON_COMPETITIVE_TYPES:
            return {"is_competitive": False, "outcome": None, "points": {}, "payload": {}}

        if qtype == "multiple_choice":
            outcome = scoring.compute_score(
                "exact_match",
                value_a=sub_a.payload.get("answer_option"),
                value_b=sub_b.payload.get("answer_option"),
            )
            pts = 1 if outcome["matched"] else 0
            return {
                "is_competitive": True,
                "outcome": outcome["outcome"],
                "points": {str(user_a.id): pts, str(user_b.id): pts},
                "payload": {},
            }

        if qtype == "rating":
            outcome = scoring.compute_score(
                "rating_difference",
                value_a=sub_a.payload.get("answer_option"),
                value_b=sub_b.payload.get("answer_option"),
            )
            pts = outcome["points_each"]
            return {
                "is_competitive": True,
                "outcome": outcome["outcome"],
                "points": {str(user_a.id): pts, str(user_b.id): pts},
                "payload": {},
            }

        if qtype == "prediction":
            # Both directions are judged independently: did A correctly
            # guess B's real answer, and separately did B correctly guess
            # A's real answer.
            a_guessed_b = scoring.compute_score(
                "prediction",
                predicted=sub_a.payload.get("predicted_option"),
                actual=sub_b.payload.get("answer_option"),
            )
            b_guessed_a = scoring.compute_score(
                "prediction",
                predicted=sub_b.payload.get("predicted_option"),
                actual=sub_a.payload.get("answer_option"),
            )
            if a_guessed_b["correct"] and b_guessed_a["correct"]:
                outcome = "both_correct"
            elif not a_guessed_b["correct"] and not b_guessed_a["correct"]:
                outcome = "both_incorrect"
            else:
                outcome = "one_correct"
            return {
                "is_competitive": True,
                "outcome": outcome,
                "points": {
                    str(user_a.id): 1 if a_guessed_b["correct"] else 0,
                    str(user_b.id): 1 if b_guessed_a["correct"] else 0,
                },
                "payload": {
                    "predictions": {
                        str(user_a.id): {"correct": a_guessed_b["correct"]},
                        str(user_b.id): {"correct": b_guessed_a["correct"]},
                    }
                },
            }

        raise ActivityValidationError(f"Unsupported classic question_type for scoring: {qtype!r}")
