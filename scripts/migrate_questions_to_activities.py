"""
One-off backfill: creates an ActivityContent(activity_type="classic_question")
row for every legacy Question row, so the Activity system can serve them
(see app/services/activities/classic_question.py and
app/routes/activities.py's play_legacy_question, which looks up content by
payload["legacy_question_id"]).

Safe to re-run - skips any Question that already has a matching
ActivityContent, so running it twice won't create duplicates.

Usage (make sure DATABASE_URL is set to whichever database you want to
migrate - local dev or your real Supabase database - before running):

    set DATABASE_URL=<your connection string>
    python scripts/migrate_questions_to_activities.py
"""

from app import create_app
from app.extensions import db
from app.models import ActivityContent, Question


def existing_legacy_ids():
    """legacy_question_id values already migrated, so this script is safe
    to run more than once without creating duplicates."""
    ids = set()
    for content in ActivityContent.query.filter_by(activity_type="classic_question").all():
        legacy_id = content.payload.get("legacy_question_id")
        if legacy_id is not None:
            ids.add(legacy_id)
    return ids


def migrate():
    already_done = existing_legacy_ids()
    questions = Question.query.all()

    created = 0
    skipped = 0

    for q in questions:
        if q.id in already_done:
            skipped += 1
            continue

        content = ActivityContent(
            activity_type="classic_question",
            category=q.category,
            prompt=q.text,
            spicy_level=q.spicy_level,
            match_eligible=q.match_eligible,
            active=q.active,
        )
        content.payload = {
            "question_type": q.question_type,
            "options": q.options,
            "predict_text": q.predict_text,
            "legacy_question_id": q.id,
        }
        db.session.add(content)
        created += 1

    db.session.commit()
    print(
        f"Migration complete: created {created} new ActivityContent rows, "
        f"skipped {skipped} already-migrated questions. Total Questions: {len(questions)}."
    )


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        migrate()
