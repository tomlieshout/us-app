from app.extensions import db
from app.models import Question, Round


def _play_prediction_round(app, tom, sarah, tom_guess_matches=True):
    with app.app_context():
        q = Question.query.filter_by(question_type="prediction").first()
        options = q.options
        from app.models import Couple

        couple_row = Couple.query.first()
        r = Round(couple_id=couple_row.id, question_id=q.id)
        db.session.add(r)
        db.session.commit()
        round_id = r.id
        opts = options

    tom_actual = opts[0]
    sarah_actual = opts[1]
    tom_guess = sarah_actual if tom_guess_matches else opts[2]

    tom.post("/api/answers", json={"round_id": round_id, "answer_option": tom_actual, "predicted_option": tom_guess})
    resp = sarah.post(
        "/api/answers",
        json={"round_id": round_id, "answer_option": sarah_actual, "predicted_option": opts[0]},
    )
    return round_id, resp.get_json()


def test_prediction_scoring_correct_and_incorrect(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]
    round_id, revealed = _play_prediction_round(app, tom, sarah, tom_guess_matches=True)
    assert revealed["prediction"]["partner_guessed_correctly"] in (True, False)

    tom_view = tom.get(f"/api/rounds/{round_id}").get_json()
    assert tom_view["prediction"]["i_guessed_correctly"] is True


def test_prediction_percent_hidden_until_minimum_rounds(app, couple):
    tom, sarah = couple["tom"], couple["sarah"]

    stats = tom.get("/api/stats").get_json()
    assert stats["prediction"]["percent"] is None
    assert stats["prediction"]["enough_data"] is False

    # MIN_ROUNDS_FOR_PREDICTION_PERCENT defaults to 5 in TestingConfig's base
    for i in range(5):
        with app.app_context():
            q = Question.query.filter_by(question_type="prediction").offset(i).first()
        _play_one_more_prediction(app, tom, sarah, q)

    stats = tom.get("/api/stats").get_json()
    assert stats["prediction"]["enough_data"] is True
    assert isinstance(stats["prediction"]["percent"], int)


def _play_one_more_prediction(app, tom, sarah, question):
    with app.app_context():
        from app.models import Couple

        couple_row = Couple.query.first()
        r = Round(couple_id=couple_row.id, question_id=question.id)
        db.session.add(r)
        db.session.commit()
        round_id = r.id
        opts = question.options

    tom.post("/api/answers", json={"round_id": round_id, "answer_option": opts[0], "predicted_option": opts[1]})
    sarah.post("/api/answers", json={"round_id": round_id, "answer_option": opts[1], "predicted_option": opts[0]})
