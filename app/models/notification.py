"""
In-app notifications: a small, per-recipient feed of concise nudges,
covering game_answered, game_ready, appreciation_received, plan_added,
shared_match, and new_champion. See app/services/notifications.py for
where each type gets created and why - deliberately from the request
routes that own each triggering event, not from deeper service/model
code, so a maintenance operation like
scripts/backfill_activity_results.py (which also calls handler.reveal())
never floods the feed with notifications for old, already-happened
activity.

Kept as its own small table rather than folding into any existing model
because the six event types don't share a natural home: some are tied to
a specific row (an Activity, an Appreciation, a Plan), and "new_champion"
isn't tied to any row at all - it's a transition in a live-computed
value (see app/services/stats.py's compute_competitive_stats) that has
nowhere else to be persisted the moment it's detected.
"""

from datetime import datetime

from app.extensions import db

NOTIFICATION_TYPES = [
    "game_answered",
    "game_ready",
    "appreciation_received",
    "plan_added",
    "shared_match",
    "new_champion",
]

# "Keep notifications concise" - enforced in app/services/notifications.py,
# not just a style guideline.
MAX_TEXT_LENGTH = 140


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    type = db.Column(db.String(32), nullable=False)
    text = db.Column(db.String(MAX_TEXT_LENGTH), nullable=False)

    # Only set for game_answered/game_ready - which tab a tap should open
    # (Questions for classic_question, Games for everything else). Not a
    # generic "reference_id" pointing at a row, by design: tapping a
    # notification opens the relevant tab, not the exact activity - see
    # app/static/js/views/notifications.js for why.
    activity_type = db.Column(db.String(32), nullable=True)

    is_seen = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    couple = db.relationship("Couple", backref=db.backref("notifications", lazy="dynamic"))
    recipient = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "activity_type": self.activity_type,
            "is_seen": self.is_seen,
            "created_at": self.created_at.isoformat() + "Z",
        }
