"""
Challenges: reuses ActivityContent for the challenge bank (category-
tagged, randomly selectable text - the same "reusable content" concept
every other game's seed bank already is), but does NOT use
Activity/ActivitySubmission/ActivityResult/ActivityHandler for the
per-couple lifecycle. There's no privacy dimension here at all - both
partners see the same challenge, nothing is hidden or revealed - so the
submit-then-reveal shape those classes exist for simply doesn't apply.
The actual lifecycle (accept -> maybe wait on a second confirmation ->
complete) needed its own small model, same reasoning that gave 20
Questions its own dedicated structure.

Skipping IS persisted (status="skipped"). This is a deliberate reversal
of this module's earlier design, which kept skips stateless on purpose
("no record of a skip to nag anyone about later") - see git history if
you want the original reasoning. The couple now explicitly wants
accepted-or-skipped to mean "don't show me this again," which requires
tracking it.

Cycles: because skip/accept are now permanent, a couple can run out of
untouched content in a category. Rather than deleting history to allow
replaying, each (couple, category) has a "current cycle" counter
(CoupleChallengeCycle). A CoupleChallenge row is stamped with the cycle
it was created in. Only rows matching the CURRENT cycle for their
content's category count as "already engaged" when building the
suggestion pool - see app/services/challenges.py. Replaying a category
just increments its cycle counter; every prior row is left untouched as
permanent history, and simply stops counting against the fresh pool.
"""

import json
from datetime import datetime

from app.extensions import db

CHALLENGE_CATEGORIES = ["cute", "funny", "deep", "romantic", "spicy", "longdistance"]

# Categories gated behind the couple's dual Spicy opt-in, and excluded
# from the unfiltered "All" tab the same way. Long Distance content is
# just as explicit as regular Spicy - it's simply usable while apart -
# so it gets identical gating under its own tab rather than being folded
# into "spicy" or left ungated.
SPICY_GATED_CATEGORIES = {"spicy", "longdistance"}


class CoupleChallenge(db.Model):
    __tablename__ = "couple_challenges"
    __table_args__ = (
        db.UniqueConstraint(
            "couple_id", "content_id", "cycle", name="uq_couple_challenge_content_cycle"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey("activity_contents.id"), nullable=False)

    # Which replay cycle (for this content's category) this row belongs
    # to. Defaults to 1 - the couple's first time through a category,
    # before any replay has ever happened. See module docstring.
    cycle = db.Column(db.Integer, nullable=False, default=1, server_default="1")

    # accepted | completed | skipped
    status = db.Column(db.String(16), nullable=False, default="accepted")

    # Snapshotted from the content at accept/skip time, so this stays
    # stable even if the seed data changes later.
    requires_both = db.Column(db.Boolean, nullable=False, default=False)

    # JSON list of user_ids who have confirmed their part done. For a
    # solo challenge this jumps straight from [] to [user_id] and
    # status becomes "completed" immediately. For a requires_both
    # challenge, status only becomes "completed" once both couple
    # members' ids are present. Always [] for a skipped row.
    completed_by_json = db.Column(db.Text, nullable=True)

    accepted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    couple = db.relationship("Couple", backref=db.backref("challenges", lazy="dynamic"))
    content = db.relationship("ActivityContent")

    @property
    def completed_by(self):
        if not self.completed_by_json:
            return []
        return json.loads(self.completed_by_json)

    @completed_by.setter
    def completed_by(self, value):
        self.completed_by_json = json.dumps(value)


class CoupleChallengeCycle(db.Model):
    """One row per (couple, category) that has ever been replayed or
    engaged with. Absence of a row means "cycle 1, never replayed" -
    callers should treat a missing row as current_cycle=1 rather than
    eagerly creating one, so a couple that never replays anything never
    accumulates rows here at all."""

    __tablename__ = "couple_challenge_cycles"
    __table_args__ = (
        db.UniqueConstraint("couple_id", "category", name="uq_couple_challenge_cycle_category"),
    )

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    category = db.Column(db.String(32), nullable=False)
    current_cycle = db.Column(db.Integer, nullable=False, default=1)

    couple = db.relationship("Couple", backref=db.backref("challenge_cycles", lazy="dynamic"))
