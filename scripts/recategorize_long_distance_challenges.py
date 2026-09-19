"""
One-off fix-up script - only needed if you already ran seed.py against
the previous version of challenges_data.py, where the long-distance
challenges were still tagged category="spicy" before this change split
them into their own "longdistance" category.

seed.py is insert-only and matches on exact prompt text: since these
prompts already exist in the database, re-running seed.py after this
edit will NOT update their category - it'll just see "prompt already
exists" and skip them, leaving them stuck under "spicy". This script
fixes that directly: it finds rows matching the current long-distance
prompts in seed/challenges_data.py that are still sitting under
"spicy", and moves them to "longdistance".

Safe to run even if you never deployed the old version - it'll just
report nothing to fix.

Usage, from the project root (same folder as run.py):
    python scripts\\recategorize_long_distance_challenges.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run import app
from app.extensions import db
from app.models import ActivityContent
from seed.challenges_data import CHALLENGES

long_distance_prompts = {c["prompt"] for c in CHALLENGES if c["category"] == "longdistance"}

with app.app_context():
    if not long_distance_prompts:
        print("No 'longdistance' entries found in seed/challenges_data.py - nothing to do.")
    else:
        matched = ActivityContent.query.filter(
            ActivityContent.activity_type == "challenge",
            ActivityContent.category == "spicy",
            ActivityContent.prompt.in_(long_distance_prompts),
        ).all()

        if not matched:
            print("Nothing to recategorize - no matching rows found under 'spicy'.")
        else:
            print(f"Found {len(matched)} challenge(s) still under 'spicy' that belong in 'longdistance':\n")
            for c in matched:
                print(" -", c.prompt)
            db.session.bulk_update_mappings(
                ActivityContent, [{"id": c.id, "category": "longdistance"} for c in matched]
            )
            db.session.commit()
            print(f"\nDone - moved {len(matched)} challenge(s) to 'longdistance'.")
