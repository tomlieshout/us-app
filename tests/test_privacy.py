from tests.conftest import join_couple, register_couple


def _get_daily_round_id(client):
    resp = client.get("/api/rounds/current")
    assert resp.status_code == 200
    return resp.get_json()["round_id"], resp.get_json()["question"]


def _answer(client, round_id, question, value_index=0):
    """Answers a round regardless of its question_type, picking a valid value."""
    payload = {"round_id": round_id}
    qtype = question["question_type"]
    if qtype == "free_text":
        payload["answer_text"] = "Japan" if value_index == 0 else "Italy"
    elif qtype in ("multiple_choice", "rating", "structured_scale"):
        payload["answer_option"] = question["options"][value_index % len(question["options"])]
    elif qtype == "prediction":
        options = question["options"]
        payload["answer_option"] = options[value_index % len(options)]
        payload["predicted_option"] = options[(value_index + 1) % len(options)]
    return client.post("/api/answers", json=payload)


def test_full_scenario_from_brief(couple):
    """Mirrors section 58 of the build brief almost line for line."""
    tom, sarah = couple["tom"], couple["sarah"]

    round_id_tom, question_tom = _get_daily_round_id(tom)
    round_id_sarah, question_sarah = _get_daily_round_id(sarah)
    assert round_id_tom == round_id_sarah  # same shared daily question

    resp = _answer(tom, round_id_tom, question_tom, value_index=0)
    assert resp.status_code == 201
    tom_view = resp.get_json()
    assert tom_view["my_answered"] is True
    assert tom_view["revealed"] is False
    assert "partner_answer" not in tom_view

    resp = sarah.get(f"/api/rounds/{round_id_sarah}")
    sarah_view = resp.get_json()
    assert sarah_view["partner_answered"] is True
    assert sarah_view["revealed"] is False
    assert "partner_answer" not in sarah_view
    body_text = str(sarah_view)
    assert "Japan" not in body_text

    resp = _answer(sarah, round_id_sarah, question_sarah, value_index=1)
    assert resp.status_code == 201
    sarah_view = resp.get_json()
    assert sarah_view["revealed"] is True
    assert sarah_view["partner_answer"] is not None

    tom_final = tom.get(f"/api/rounds/{round_id_tom}").get_json()
    assert tom_final["revealed"] is True
    assert tom_final["my_answer"] is not None
    assert tom_final["partner_answer"] is not None

    resp = _answer(tom, round_id_tom, question_tom, value_index=0)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "duplicate_answer"

    partner_answer_id = tom_final["partner_answer"]["id"]
    resp = tom.post("/api/reactions", json={"answer_id": partner_answer_id, "reaction_type": "love"})
    assert resp.status_code == 201

    sarah_final = sarah.get(f"/api/rounds/{round_id_sarah}").get_json()
    reactions_on_my_answer = sarah_final["reactions"]["on_my_answer"]
    assert any(r["reaction_type"] == "love" for r in reactions_on_my_answer)

    resp = sarah.post("/api/comments", json={"round_id": round_id_sarah, "comment_text": "I knew it!"})
    assert resp.status_code == 201
    tom_comments = tom.get(f"/api/comments/{round_id_tom}").get_json()["comments"]
    assert any(c["comment_text"] == "I knew it!" for c in tom_comments)


def test_cannot_comment_before_reveal(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    round_id, question = _get_daily_round_id(tom)
    _answer(tom, round_id, question, value_index=0)

    resp = tom.post("/api/comments", json={"round_id": round_id, "comment_text": "hi"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "not_revealed"


def test_cross_couple_isolation(app, couple):
    tom = couple["tom"]
    round_id, question = _get_daily_round_id(tom)
    _answer(tom, round_id, question, value_index=0)

    other_client_a = app.test_client()
    other_client_b = app.test_client()
    resp = register_couple(other_client_a, name="Alex", username="alex")
    invite_code = resp.get_json()["couple"]["invite_code"]
    join_couple(other_client_b, invite_code, name="Jamie", username="jamie")

    resp = other_client_a.get(f"/api/rounds/{round_id}")
    assert resp.status_code == 404

    resp = other_client_a.post("/api/answers", json={"round_id": round_id, "answer_text": "Nope"})
    assert resp.status_code == 404

    resp = other_client_a.get(f"/api/comments/{round_id}")
    assert resp.status_code == 404
