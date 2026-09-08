"""
Centralized scoring. This module is the ONLY place point values get
decided anywhere in the new Activity system - activity handlers call into
it, they never invent points themselves, and nothing here ever reads a
score, point value, or outcome from client input. Every function takes
already-validated, already-persisted submission values and returns a
result computed purely server-side.

Rules implemented (from the Building Us spec):
    - Exact match (Would You Rather, and classic multiple-choice questions
      with no "correct" answer): match = +1 each, no match = +0 each.
    - Prediction / multiple choice prediction: correct = +1, incorrect = +0.
    - Rating difference (1-10 scales): exact = +2 each, within 1 = +1 each,
      more than 1 apart = +0 each.

New games get new scoring by adding a function here and registering it in
SCORING_FUNCTIONS - existing callers and existing scoring are untouched.
"""


def score_exact_match(value_a, value_b):
    """+1 each on an exact match, +0 each otherwise. Used for Would You
    Rather, and for classic multiple-choice questions that are just each
    partner's own pick compared to the other's (no "correct" answer)."""
    matched = value_a is not None and value_b is not None and value_a == value_b
    return {"outcome": "match" if matched else "no_match", "matched": matched}


def score_prediction(predicted, actual):
    """+1 for a correct prediction of the partner's real answer, +0
    otherwise. This is a one-directional check - a symmetric "did we both
    guess correctly" situation is two calls to this, one per direction."""
    correct = predicted is not None and actual is not None and predicted == actual
    return {"outcome": "correct" if correct else "incorrect", "correct": correct}


def score_rating_difference(value_a, value_b):
    """Exact match: +2 each. Within 1: +1 each. More than 1 apart: +0 each.
    Values are the numeric-string options rating-type content uses
    (e.g. "1".."10"); non-numeric input scores as no points rather than
    raising, since a malformed value should never be able to crash a
    reveal."""
    try:
        a, b = int(value_a), int(value_b)
    except (TypeError, ValueError):
        return {"outcome": None, "points_each": 0}
    diff = abs(a - b)
    if diff == 0:
        return {"outcome": "exact", "points_each": 2}
    if diff == 1:
        return {"outcome": "close", "points_each": 1}
    return {"outcome": "different", "points_each": 0}


# Registry so a future game-specific scorer can be added (new function +
# one line here) without any existing caller needing to change.
SCORING_FUNCTIONS = {
    "exact_match": score_exact_match,
    "prediction": score_prediction,
    "rating_difference": score_rating_difference,
}


def compute_score(scoring_type, **kwargs):
    fn = SCORING_FUNCTIONS.get(scoring_type)
    if fn is None:
        raise ValueError(f"Unknown scoring_type: {scoring_type!r}")
    return fn(**kwargs)
