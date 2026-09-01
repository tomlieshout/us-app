from datetime import timedelta

from app.models import Answer, DailySelection, Favourite, Reaction, Round
from app.services.prediction import prediction_accuracy
from app.services.questions import couple_local_today


def compute_streaks(couple):
    """Streaks are based on the shared daily question: a day "counts" once
    that day's daily round has been revealed (both partners answered)."""
    selections = (
        DailySelection.query.filter_by(couple_id=couple.id).order_by(DailySelection.date.asc()).all()
    )
    completed_dates = sorted({s.date for s in selections if s.round and s.round.is_revealed})

    if not completed_dates:
        return {"current_streak": 0, "longest_streak": 0}

    longest = 1
    run = 1
    for i in range(1, len(completed_dates)):
        if (completed_dates[i] - completed_dates[i - 1]).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)

    date_set = set(completed_dates)
    today = couple_local_today(couple)
    check_day = today if today in date_set else today - timedelta(days=1)
    current = 0
    while check_day in date_set:
        current += 1
        check_day -= timedelta(days=1)

    return {"current_streak": current, "longest_streak": longest}


def compute_couple_stats(user, min_rounds_for_percent=5):
    couple = user.couple
    today = couple_local_today(couple)
    week_start = today - timedelta(days=today.weekday())

    revealed_rounds = couple.rounds.filter(Round.revealed_at.isnot(None))
    questions_answered = revealed_rounds.count()
    this_week = revealed_rounds.filter(Round.revealed_at >= week_start).count()

    favourites_count = Favourite.query.filter_by(user_id=user.id).count()

    # Reactions exchanged = reactions on any answer belonging to a round in
    # this couple (either direction).
    reactions_exchanged = (
        Reaction.query.join(Answer, Reaction.answer_id == Answer.id)
        .join(Round, Answer.round_id == Round.id)
        .filter(Round.couple_id == couple.id)
        .count()
    )

    streaks = compute_streaks(couple)
    prediction = prediction_accuracy(user, min_rounds_for_percent=min_rounds_for_percent)

    return {
        "questions_answered": questions_answered,
        "questions_this_week": this_week,
        "favourites_count": favourites_count,
        "reactions_exchanged": reactions_exchanged,
        "current_streak": streaks["current_streak"],
        "longest_streak": streaks["longest_streak"],
        "prediction": prediction,
    }
