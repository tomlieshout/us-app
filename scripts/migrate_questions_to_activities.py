"""
One-off DATA migration (not a schema/Alembic migration - this writes rows,
it doesn't change table structure) that copies the existing Question /
Round / Answer content into the new Activity / ActivityContent /
ActivitySubmission tables, so the new system has the full legacy content
and history available to build on.

Non-destructive by design:
  - Only ever INSERTs into the four activity_* tables.
  - Never UPDATEs, DELETEs, or otherwise touches Question / Round / Answer /
    Couple / User rows. Nothing here can lose or corrupt existing data.
  - Safe to re-run: every migrated row carries a "legacy_*_id" pointer in
    its JSON payload/state, and the script skips anything already migrated
    (matched by that pointer) instead of duplicating it.
  - Supports --dry-run: builds and validates everything exactly as a real
    run would (so it also catches referential-integrity problems), then
    rolls back instead of committing.

Every legacy Question becomes one ActivityContent row with
activity_type = "classic_question" - a single deliberate umbrella type.
The original question_type (free_text / multiple_choice / prediction /
rating / structured_scale) is preserved *inside* the new row's payload
rather than mapped onto a different new activity_type, so nothing is lost
or silently reinterpreted. Deciding whether "classic_question" prediction
content should later be treated as the new first-class "prediction"
activity_type is a product decision for a later phase, not something this
copy step should quietly decide on its own.

ActivityResult is intentionally left untouched by this script. The legacy
system has no persisted scoring/result to copy (prediction accuracy is
computed live, on demand, in services/prediction.py) - inventing
ActivityResult rows here would mean computing new derived data, not copying
existing data, which is outside what was asked for.

Usage:
    python scripts/migrate_questions_to_activities.py [--dry-run]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Activity, ActivityContent, ActivitySubmission, Answer, Question, Round  # noqa: E402


def _legacy_question_ids_already_migrated():
    mapping = {}
    for c in ActivityContent.query.filter_by(activity_type="classic_question").all():
        legacy_id = c.payload.get("legacy_question_id")
        if legacy_id is not None:
            mapping[legacy_id] = c.id
    return mapping


def _legacy_round_ids_already_migrated():
    mapping = {}
    for a in Activity.query.all():
        legacy_id = a.state.get("legacy_round_id")
        if legacy_id is not None:
            mapping[legacy_id] = a.id
    return mapping


def _legacy_answer_ids_already_migrated():
    ids = set()
    for s in ActivitySubmission.query.all():
        legacy_id = s.payload.get("legacy_answer_id")
        if legacy_id is not None:
            ids.add(legacy_id)
    return ids


def migrate():
    """Runs the copy. Caller decides commit vs rollback (see __main__) so
    --dry-run and a real run share the exact same code path, including
    constraint validation via flush()."""
    stats = {
        "questions_total": Question.query.count(),
        "questions_migrated": 0,
        "questions_already_migrated": 0,
        "rounds_total": Round.query.count(),
        "rounds_migrated": 0,
        "rounds_already_migrated": 0,
        "answers_total": Answer.query.count(),
        "answers_migrated": 0,
        "answers_already_migrated": 0,
    }

    question_id_to_content_id = _legacy_question_ids_already_migrated()
    stats["questions_already_migrated"] = len(question_id_to_content_id)

    for q in Question.query.order_by(Question.id.asc()).all():
        if q.id in question_id_to_content_id:
            continue
        content = ActivityContent(
            activity_type="classic_question",
            category=q.category,
            prompt=q.text,
            spicy_level=q.spicy_level,
            match_eligible=q.match_eligible,
            active=q.active,
            created_at=q.created_at,  # preserve the original timestamp, not "now"
        )
        content.payload = {
            "legacy_question_id": q.id,
            "question_type": q.question_type,
            "options": q.options,
            "predict_text": q.predict_text,
        }
        db.session.add(content)
        db.session.flush()  # assigns content.id so rounds below can link to it
        question_id_to_content_id[q.id] = content.id
        stats["questions_migrated"] += 1

    round_id_to_activity_id = _legacy_round_ids_already_migrated()
    stats["rounds_already_migrated"] = len(round_id_to_activity_id)

    for r in Round.query.order_by(Round.id.asc()).all():
        if r.id in round_id_to_activity_id:
            continue
        content_id = question_id_to_content_id.get(r.question_id)
        if content_id is None:
            raise RuntimeError(
                f"Round {r.id} references question {r.question_id}, which has no "
                "migrated ActivityContent - aborting rather than guessing."
            )
        activity = Activity(
            couple_id=r.couple_id,
            content_id=content_id,
            is_daily=r.is_daily,
            created_at=r.created_at,
            revealed_at=r.revealed_at,  # preserved as-is, including None for unrevealed rounds
        )
        activity.state = {"legacy_round_id": r.id}
        db.session.add(activity)
        db.session.flush()
        round_id_to_activity_id[r.id] = activity.id
        stats["rounds_migrated"] += 1

    already_answer_ids = _legacy_answer_ids_already_migrated()
    stats["answers_already_migrated"] = len(already_answer_ids)

    for ans in Answer.query.order_by(Answer.id.asc()).all():
        if ans.id in already_answer_ids:
            continue
        activity_id = round_id_to_activity_id.get(ans.round_id)
        if activity_id is None:
            raise RuntimeError(
                f"Answer {ans.id} references round {ans.round_id}, which has no "
                "migrated Activity - aborting rather than guessing."
            )
        submission = ActivitySubmission(
            activity_id=activity_id,
            user_id=ans.user_id,
            is_private=ans.is_private,
            created_at=ans.created_at,
            updated_at=ans.updated_at,
        )
        submission.payload = {
            "legacy_answer_id": ans.id,
            "answer_text": ans.answer_text,
            "answer_option": ans.answer_option,
            "predicted_option": ans.predicted_option,
        }
        db.session.add(submission)
        stats["answers_migrated"] += 1

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Validate and report, but write nothing")
    args = parser.parse_args()

    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        result = migrate()
        if args.dry_run:
            db.session.rollback()
        else:
            db.session.commit()

        print(("DRY RUN (nothing written) - " if args.dry_run else "") + "Migration summary:")
        for key, value in result.items():
            print(f"  {key}: {value}")
