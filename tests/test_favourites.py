def test_favourite_add_list_remove(couple):
    tom = couple["tom"]
    questions = tom.get("/api/questions?category=relationship").get_json()["questions"]
    q_id = questions[0]["id"]

    resp = tom.post("/api/favourites", json={"question_id": q_id})
    assert resp.status_code == 201

    favs = tom.get("/api/favourites").get_json()["favourites"]
    assert any(f["id"] == q_id for f in favs)

    resp = tom.delete(f"/api/favourites/{q_id}")
    assert resp.status_code == 200
    favs = tom.get("/api/favourites").get_json()["favourites"]
    assert not any(f["id"] == q_id for f in favs)


def test_favourites_are_per_user(couple):
    tom, sarah = couple["tom"], couple["sarah"]
    questions = tom.get("/api/questions?category=deep").get_json()["questions"]
    q_id = questions[0]["id"]

    tom.post("/api/favourites", json={"question_id": q_id})

    sarah_favs = sarah.get("/api/favourites").get_json()["favourites"]
    assert not any(f["id"] == q_id for f in sarah_favs)
