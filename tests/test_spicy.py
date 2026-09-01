def test_spicy_locked_by_default(couple):
    tom = couple["tom"]
    resp = tom.get("/api/questions?category=spicy")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "spicy_locked"

    resp = tom.get("/api/rounds/random?category=spicy")
    assert resp.status_code == 403


def test_spicy_requires_both_partners_to_opt_in(couple):
    tom, sarah = couple["tom"], couple["sarah"]

    resp = tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    assert resp.status_code == 200
    assert resp.get_json()["couple"]["spicy_unlocked"] is False  # Sarah hasn't opted in yet

    resp = tom.get("/api/questions?category=spicy")
    assert resp.status_code == 403

    resp = sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    assert resp.get_json()["couple"]["spicy_unlocked"] is True

    resp = tom.get("/api/questions?category=spicy")
    assert resp.status_code == 200
    assert len(resp.get_json()["questions"]) > 0


def test_spicy_opt_in_requires_adult_confirmation(couple):
    tom = couple["tom"]
    resp = tom.post("/api/settings/spicy", json={"enabled": True})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "confirmation_required"


def test_either_partner_can_disable_spicy(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    resp = sarah.post("/api/settings/spicy", json={"enabled": False})
    assert resp.get_json()["couple"]["spicy_unlocked"] is False

    resp = tom.get("/api/questions?category=spicy")
    assert resp.status_code == 403


def test_private_spicy_answer_hidden_from_partner(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    tom.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})
    sarah.post("/api/settings/spicy", json={"enabled": True, "adult_confirmation": True})

    questions = tom.get("/api/questions?category=spicy").get_json()["questions"]
    free_text_q = next(q for q in questions if q["question_type"] == "free_text")

    played = tom.post(f"/api/questions/{free_text_q['id']}/play").get_json()
    round_id = played["round_id"]

    tom.post("/api/answers", json={"round_id": round_id, "answer_text": "Something private", "is_private": True})
    sarah.post("/api/answers", json={"round_id": round_id, "answer_text": "My honest answer"})

    sarah_view = sarah.get(f"/api/rounds/{round_id}").get_json()
    assert sarah_view["partner_answer"]["is_private"] is True
    assert "text" not in sarah_view["partner_answer"]
    assert "Something private" not in str(sarah_view)

    # Tom can still see his own answer content
    tom_view = tom.get(f"/api/rounds/{round_id}").get_json()
    assert tom_view["my_answer"]["text"] == "Something private"
