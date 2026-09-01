import pytest

from app import create_app
from app.extensions import db as _db


@pytest.fixture()
def app():
    """Important: we only hold the app context open for setup/teardown, NOT
    for the whole test body. If we kept it open across the test, every
    simulated request from every test client would share one persistent
    SQLAlchemy session/identity-map (Flask reuses an already-active app
    context instead of pushing a fresh one per request) - which doesn't
    match production, where each real request gets its own session, and it
    can hide or fake privacy bugs in tests. Popping the context after setup
    forces each client.get()/post() call below to get a fresh request (and
    therefore app) context, exactly like real traffic."""
    flask_app = create_app("testing")
    with flask_app.app_context():
        _db.create_all()
        _seed_test_questions()

    yield flask_app

    with flask_app.app_context():
        _db.session.remove()
        _db.drop_all()


def _seed_test_questions():
    """Loads the real question bank into the test database so every
    category/question_type has realistic data to exercise, exactly like
    seed/seed.py does for local/production databases."""
    from app.models import Question
    from seed.seed_questions import QUESTIONS

    for entry in QUESTIONS:
        question = Question(
            text=entry["text"],
            predict_text=entry.get("predict_text"),
            category=entry["category"],
            question_type=entry["qtype"],
            spicy_level=entry.get("spicy_level"),
            match_eligible=entry.get("match_eligible", False),
            active=True,
        )
        if "options" in entry:
            question.options = entry["options"]
        _db.session.add(question)
    _db.session.commit()


@pytest.fixture()
def client(app):
    return app.test_client()


def register_couple(client, name="Tom", username="tom", password="password1234", email=None):
    return client.post(
        "/api/auth/register-couple",
        json={"name": name, "username": username, "password": password, "email": email},
    )


def join_couple(client, invite_code, name="Sarah", username="sarah", password="password1234", email=None):
    return client.post(
        "/api/auth/join-couple",
        json={
            "name": name,
            "username": username,
            "password": password,
            "invite_code": invite_code,
            "email": email,
        },
    )


@pytest.fixture()
def couple(app):
    """A complete two-member couple, each with their own logged-in test
    client (simulating two separate phones)."""
    client_a = app.test_client()
    client_b = app.test_client()

    resp_a = register_couple(client_a, name="Tom", username="tom")
    invite_code = resp_a.get_json()["couple"]["invite_code"]

    join_couple(client_b, invite_code, name="Sarah", username="sarah")

    return {"tom": client_a, "sarah": client_b}
