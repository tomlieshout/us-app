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

Random selection ("show me a candidate") is deliberately stateless -
skipping a suggested challenge writes nothing to the database at all,
matching "do not make challenges mandatory": there's no record of a skip
to nag anyone about later. A row only gets created on ACCEPT.
"""

import json
from datetime import datetime

from app.extensions import db

CHALLENGE_CATEGORIES = ["cute", "funny", "deep", "romantic"]


class CoupleChallenge(db.Model):
    __tablename__ = "couple_challenges"
    __table_args__ = (db.UniqueConstraint("couple_id", "content_id", name="uq_couple_challenge_content"),)

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey("activity_contents.id"), nullable=False)

    # accepted | completed - no "skipped" status is ever persisted, see
    # module docstring.
    status = db.Column(db.String(16), nullable=False, default="accepted")

    # Snapshotted from the content at accept time, so this stays stable
    # even if the seed data changes later.
    requires_both = db.Column(db.Boolean, nullable=False, default=False)

    # JSON list of user_ids who have confirmed their part done. For a
    # solo challenge this jumps straight from [] to [user_id] and
    # status becomes "completed" immediately. For a requires_both
    # challenge, status only becomes "completed" once both couple
    # members' ids are present.
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
