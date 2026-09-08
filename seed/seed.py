"""
Populates the legacy questions table from seed/seed_questions.py, AND the
new ActivityContent table for any activity_type that only ever lives in
the new system (currently: would_you_rather, from seed/wyr_questions.py -
there's no legacy equivalent to migrate for a game that never existed in
the old system).

Usage (from the project root, with your venv active):
    python seed/seed.py

Safe to re-run: everything here matches on exact content before inserting,
so it only ever adds what's missing. This is how you add new questions or
new Would You Rather prompts later without touching any application code -
just add entries to the relevant data file and run this again.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import ActivityContent, Question  # noqa: E402
from seed.seed_questions import QUESTIONS  # noqa: E402
from seed.wyr_questions import WOULD_YOU_RATHER_QUESTIONS  # noqa: E402
from seed.know_each_other_questions import KNOW_EACH_OTHER_QUESTIONS  # noqa: E402
from seed.emoji_story_questions import EMOJI_STORY_GUESS_STORIES  # noqa: E402
from seed.who_would_questions import WHO_WOULD_QUESTIONS  # noqa: E402
from seed.challenges_data import CHALLENGES  # noqa: E402


def seed_legacy_questions():
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
    print(f"Legacy questions: inserted {inserted} new. {Question.query.count()} total.")


def seed_would_you_rather():
    existing = {
        c.prompt + "|" + c.payload.get("option_a", "") + "|" + c.payload.get("option_b", "")
        for c in ActivityContent.query.filter_by(activity_type="would_you_rather").all()
    }
    inserted = 0
    for entry in WOULD_YOU_RATHER_QUESTIONS:
        key = entry["prompt"] + "|" + entry["option_a"] + "|" + entry["option_b"]
        if key in existing:
            continue
        content = ActivityContent(
            activity_type="would_you_rather",
            category=entry["category"],
            prompt=entry["prompt"],
            active=True,
        )
        content.payload = {
            "option_a": entry["option_a"],
            "option_b": entry["option_b"],
            "emoji_a": entry.get("emoji_a"),
            "emoji_b": entry.get("emoji_b"),
        }
        db.session.add(content)
        inserted += 1
    db.session.commit()
    total = ActivityContent.query.filter_by(activity_type="would_you_rather").count()
    print(f"Would You Rather: inserted {inserted} new. {total} total.")


def seed_know_each_other():
    existing = {
        c.prompt + "|" + "|".join(c.payload.get("options") or [])
        for c in ActivityContent.query.filter_by(activity_type="know_each_other").all()
    }
    inserted = 0
    for entry in KNOW_EACH_OTHER_QUESTIONS:
        key = entry["prompt"] + "|" + "|".join(entry["options"])
        if key in existing:
            continue
        content = ActivityContent(
            activity_type="know_each_other",
            category=None,
            prompt=entry["prompt"],
            active=True,
        )
        content.payload = {
            "question_type": entry["question_type"],
            "options": entry["options"],
            "predict_text": entry.get("predict_text"),
        }
        db.session.add(content)
        inserted += 1
    db.session.commit()
    total = ActivityContent.query.filter_by(activity_type="know_each_other").count()
    print(f"Know Each Other: inserted {inserted} new. {total} total.")


def seed_emoji_story_guess_stories():
    existing = {
        c.payload.get("emoji_sequence")
        for c in ActivityContent.query.filter_by(activity_type="emoji_story", category="guess").all()
    }
    inserted = 0
    for entry in EMOJI_STORY_GUESS_STORIES:
        if entry["emoji_sequence"] in existing:
            continue
        content = ActivityContent(
            activity_type="emoji_story",
            category="guess",
            prompt="What's the story?",
            active=True,
        )
        content.payload = {
            "emoji_sequence": entry["emoji_sequence"],
            "explanation": entry["explanation"],
            "created_by_user_id": None,
        }
        db.session.add(content)
        inserted += 1
    db.session.commit()
    total = ActivityContent.query.filter_by(activity_type="emoji_story", category="guess").count()
    print(f"Emoji Story (guess mode): inserted {inserted} new. {total} total.")


def seed_who_would():
    existing = {
        c.prompt for c in ActivityContent.query.filter_by(activity_type="who_would").all()
    }
    inserted = 0
    for phrase in WHO_WOULD_QUESTIONS:
        prompt = f"Who would be more likely to {phrase}?"
        if prompt in existing:
            continue
        content = ActivityContent(
            activity_type="who_would",
            category=None,
            prompt=prompt,
            active=True,
        )
        content.payload = {}
        db.session.add(content)
        inserted += 1
    db.session.commit()
    total = ActivityContent.query.filter_by(activity_type="who_would").count()
    print(f"Who Would: inserted {inserted} new. {total} total.")


def seed_challenges():
    existing = {c.prompt for c in ActivityContent.query.filter_by(activity_type="challenge").all()}
    inserted = 0
    for entry in CHALLENGES:
        if entry["prompt"] in existing:
            continue
        content = ActivityContent(
            activity_type="challenge",
            category=entry["category"],
            prompt=entry["prompt"],
            active=True,
        )
        content.payload = {"requires_both": entry["requires_both"]}
        db.session.add(content)
        inserted += 1
    db.session.commit()
    total = ActivityContent.query.filter_by(activity_type="challenge").count()
    print(f"Challenges: inserted {inserted} new. {total} total.")


def run():
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        seed_legacy_questions()
        seed_would_you_rather()
        seed_know_each_other()
        seed_emoji_story_guess_stories()
        seed_who_would()
        seed_challenges()


if __name__ == "__main__":
    run()
