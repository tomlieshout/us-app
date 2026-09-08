"""
Appreciation: a short one-directional message from one partner to the
other. Deliberately NOT part of the Activity system - unlike every game
built so far, there's no privacy dimension to gate here at all. Nothing
is ever hidden between the two partners; the whole point is open,
immediate communication. So this gets its own small dedicated model,
same reasoning that gave 20 Questions and Challenges their own
structures.

No scoring, no competitive points, no relationship score - by explicit
instruction. This table has no points/score column of any kind, and
nothing here is ever meant to feed a competitive leaderboard. If a
future Stats phase wants to surface "42 appreciations sent" that belongs
under a non-competitive "Together" stat (see the Building Us doc's own
Stats section), never under "Competitive."
"""

from datetime import datetime

from app.extensions import db

MAX_MESSAGE_LENGTH = 500


class Appreciation(db.Model):
    __tablename__ = "appreciations"

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    sender_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    message_text = db.Column(db.String(MAX_MESSAGE_LENGTH), nullable=False)

    # Powers the in-app notification: an unseen appreciation is what the
    # recipient gets nudged about when they next open the app.
    is_seen = db.Column(db.Boolean, nullable=False, default=False)
    seen_at = db.Column(db.DateTime, nullable=True)

    # Recipient can pin ones that mean the most to them - separate from
    # "it's in my persistent collection," which every appreciation
    # already is by default unless deleted.
    is_kept = db.Column(db.Boolean, nullable=False, default=False)

    # Recipient's reaction - reuses the same vocabulary as
    # app.models.reaction.REACTION_TYPES for consistency (love/funny/
    # cute/surprised), just stored directly on the row since only the
    # recipient can meaningfully react to their own appreciation (no
    # need for a separate many-rows reactions table for a 1:1 case).
    reaction_type = db.Column(db.String(16), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    couple = db.relationship("Couple", backref=db.backref("appreciations", lazy="dynamic"))
    sender = db.relationship("User", foreign_keys=[sender_user_id])
    recipient = db.relationship("User", foreign_keys=[recipient_user_id])
