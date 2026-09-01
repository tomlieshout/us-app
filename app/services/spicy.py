from app.models import Question, Round
from app.models.question import INTEREST_SCALE

TOP_TIER = {"Definitely interested", "Maybe / curious"}


def _scale_distance(v1, v2):
    try:
        return abs(INTEREST_SCALE.index(v1) - INTEREST_SCALE.index(v2))
    except ValueError:
        return 0


def compute_matches(couple):
    """"Find your matches": fold every completed, match-eligible Spicy round
    into a summary that only ever exposes *overlap*, never a raw
    answer-by-answer comparison, and never a private answer either side."""
    members = couple.ordered_members()
    if len(members) != 2:
        return {"explored_together": 0, "mutual_matches": [], "mutual_interests_count": 0, "discuss_count": 0}
    u1, u2 = members

    rounds = (
        couple.rounds.join(Question)
        .filter(Question.category == "spicy", Question.match_eligible.is_(True), Round.revealed_at.isnot(None))
        .all()
    )

    matches = []
    discuss_count = 0

    for r in rounds:
        a1 = r.answer_for(u1.id)
        a2 = r.answer_for(u2.id)
        if not a1 or not a2:
            continue
        # A private answer is never used in match aggregation, in either
        # direction - not to build a match, and not to flag a "discuss" item.
        if a1.is_private or a2.is_private:
            continue
        v1, v2 = a1.answer_option, a2.answer_option
        if not v1 or not v2:
            continue
        if v1 in TOP_TIER and v2 in TOP_TIER:
            matches.append(r.question.text)
        elif _scale_distance(v1, v2) >= 2:
            # Deliberately don't say *which* topic - just that one exists,
            # so the couple can choose to talk about it without the app
            # putting either partner on the spot.
            discuss_count += 1

    return {
        "explored_together": len(rounds),
        "mutual_matches": matches,
        "mutual_interests_count": len(matches),
        "discuss_count": discuss_count,
    }
