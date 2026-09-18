"""
One-off/reusable maintenance: deactivate ActivityContent challenge rows
that have been removed from seed/challenges_data.py.

seed/seed.py only ever INSERTS (matched by exact prompt text) - it has no
mechanism to remove rows for entries deleted from the source file, so
editing challenges_data.py and re-running seed.py does nothing to rows
already in the database. This script closes that gap, the safe way: it
DEACTIVATES (active=False) rather than deletes, because:
  - it's instantly reversible (flip active back to True by hand if you
    change your mind)
  - it can never violate the couple_challenges -> activity_contents
    foreign key, even if a couple already accepted/completed one of the
    removed challenges - that row stays intact, just hidden from future
    picks. app/services/challenges.py already filters on active=True
    for both picking a random challenge AND accepting one by id, so
    deactivating is enough on its own - no other code changes needed.

A real DELETE is possible too, but isn't what this script does: if a
couple has already accepted one of the rows you're removing, deleting it
outright will either be rejected by the database (foreign key
violation) or leave that couple's already-accepted challenge pointing at
nothing, depending on your database's FK enforcement - deactivating
avoids that question entirely.

Usage (Windows):
    python scripts/deactivate_removed_challenges.py           # dry run - shows what WOULD change
    python scripts/deactivate_removed_challenges.py --apply   # actually applies it

Reads DATABASE_URL from your .env file automatically (same as run.py) -
no need to set it by hand unless you want to point at something other
than what .env already says.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# run.py (the app's actual entry point) loads .env before anything else
# reads os.environ - a plain `python scripts/whatever.py` invocation
# skips that entirely, so without this, DATABASE_URL silently falls back
# to the local sqlite:///us.db default even when a real one is sitting
# in .env right next to this script.
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import ActivityContent
from seed.challenges_data import CHALLENGES


def run(apply=False):
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    db_url = app.config["SQLALCHEMY_DATABASE_URI"]
    # Printed every run, not just on request - silently hitting the
    # wrong database is exactly the failure mode this script needs to
    # make impossible to miss.
    print(f"Using database: {db_url}\n")

    with app.app_context():
        current_prompts = {c["prompt"] for c in CHALLENGES}
        stale = (
            ActivityContent.query.filter_by(activity_type="challenge", active=True)
            .filter(~ActivityContent.prompt.in_(current_prompts))
            .all()
        )

        if not stale:
            print("Nothing to do - every active challenge row still has a matching entry in challenges_data.py.")
            return

        verb = "Deactivating" if apply else "Would deactivate"
        print(f"{verb} {len(stale)} challenge(s) no longer in challenges_data.py:")
        for c in stale:
            print(f"  [{c.id}] {c.category}: {c.prompt}")

        if apply:
            for c in stale:
                c.active = False
            db.session.commit()
            print("\nDone.")
        else:
            print("\nDry run only - nothing changed. Re-run with --apply to actually deactivate these.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually deactivate, instead of just previewing.")
    args = parser.parse_args()
    run(apply=args.apply)
