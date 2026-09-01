"""
Populates the questions table from seed/seed_questions.py.

Usage (from the project root, with your venv active):
    python seed/seed.py

Safe to re-run: matches on exact question text within a category, so it
will only insert questions that aren't already there. This is how you add
new questions later without touching any application code - just add
entries to seed_questions.py and run this again.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Question  # noqa: E402
from seed.seed_questions import QUESTIONS  # noqa: E402


def run():
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        existing = {(q.category, q.text) for q in Question.query.all()}
        inserted = 0
        for entry in QUESTIONS:
            key = (entry["category"], entry["text"])
            if key in existing:
                continue
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
            db.session.add(question)
            inserted += 1
        db.session.commit()
        total = Question.query.count()
        print(f"Seed complete: inserted {inserted} new question(s). {total} total in database.")


if __name__ == "__main__":
    run()
