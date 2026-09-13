from app.models import Question, Round


def prediction_accuracy(user, min_rounds_for_percent=5):
    """How well `user` predicts their partner's real answers, across all
    revealed 'know_me' prediction rounds this couple has played."""
    couple = user.couple
    partner = couple.other_member(user)

    result = {"rounds": 0, "correct": 0, "percent": None, "enough_data": False}
    if not partner:
        return result

    # category != "spicy" (not just == "know_me") so any future non-spicy
    # prediction category keeps counting here without another change -
    # Spicy itself is excluded regardless of lock state, matching
    # app/services/stats.py's competitive stats for the same reason.
    rounds = (
        couple.rounds.join(Question)
        .filter(Question.question_type == "prediction", Question.category != "spicy")
        .all()
    )

    total = 0
    correct = 0
    for r in rounds:
        if not r.is_revealed:
            continue
        mine = r.answer_for(user.id)
        theirs = r.answer_for(partner.id)
        if not mine or not theirs:
            continue
        if mine.predicted_option is None or theirs.answer_option is None:
            continue
        total += 1
        if mine.predicted_option == theirs.answer_option:
            correct += 1

    result["rounds"] = total
    result["correct"] = correct
    result["enough_data"] = total >= min_rounds_for_percent
    if result["enough_data"]:
        result["percent"] = round(100 * correct / total)
    return result
