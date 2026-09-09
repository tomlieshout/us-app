"""
One-off DATA backfill (not a schema/Alembic migration - writes rows, doesn't
change table structure) that computes and persists ActivityResult for
Activities that are complete (both submissions present, revealed_at set) but
never had a result computed - specifically the rows created by
scripts/migrate_questions_to_activities.py, whose own docstring explicitly
left scoring alone ("inventing ActivityResult rows here would mean computing
new derived data, not copying existing data, which is outside what was asked
for"). That's exactly what this script does instead, as its own explicit,
separately-requested step.

Non-destructive by design, same conventions as migrate_questions_to_activities.py:
  - Only ever INSERTs ActivityResult rows (via the existing handler.reveal(),
    the same code path a live submit() already uses - no scoring logic is
    duplicated here).
  - Never UPDATEs or DELETEs anything. Activity/ActivityContent/
    ActivitySubmission rows are untouched.
  - Safe to re-run: reveal() is already idempotent (returns the existing
    result without recomputing if one exists), so a second run is a no-op.
  - Supports --dry-run: computes and validates exactly as a real run would,
    then rolls back instead of committing.

Usage:
    python scripts/backfill_activity_results.py [--dry-run]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Activity, ActivityResult  # noqa: E402
from app.services.activities import get_handler  # noqa: E402


def backfill():
    stats = {"candidates": 0, "scored": 0, "skipped_incomplete": 0, "already_scored": 0}

    # revealed_at is set -> the activity was actually completed (this is how
    # the legacy Round.revealed_at was preserved by the migration script).
    # No matching ActivityResult.activity_id -> nothing has scored it yet.
    already_scored_ids = db.session.query(ActivityResult.activity_id)
    candidates = (
        Activity.query.filter(Activity.revealed_at.isnot(None))
        .filter(~Activity.id.in_(already_scored_ids))
        .all()
    )
    stats["candidates"] = len(candidates)

    for activity in candidates:
        if activity.result is not None:
            stats["already_scored"] += 1
            continue

        handler = get_handler(activity.content.activity_type)
        if not handler.is_complete(activity):
            stats["skipped_incomplete"] += 1
            continue

        handler.reveal(activity)
        stats["scored"] += 1

    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Validate and report, but write nothing")
    args = parser.parse_args()

    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        result = backfill()
        if args.dry_run:
            db.session.rollback()
        else:
            db.session.commit()

        print(("DRY RUN (nothing written) - " if args.dry_run else "") + "Backfill summary:")
        for key, value in result.items():
            print(f"  {key}: {value}")
