from datetime import datetime

from app.extensions import db


class Round(db.Model):
    """A single instance of a specific couple playing a specific question.

    The same `question_id` can be reused by many couples, or replayed later
    by the same couple, but each play-through gets its own Round row so that
    answers, reactions and comments are always scoped to one couple's one
    attempt at one question.
    """

    __tablename__ = "rounds"

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False, index=True)

    is_daily = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Set the moment the second partner's answer is submitted. Presence of
    # this timestamp is what unlocks the reveal - see services/privacy.py.
    revealed_at = db.Column(db.DateTime, nullable=True)

    couple = db.relationship("Couple", back_populates="rounds")
    question = db.relationship("Question")
    answers = db.relationship("Answer", back_populates="round", lazy="dynamic", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="round", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def is_revealed(self):
        return self.revealed_at is not None

    def answer_for(self, user_id):
        return self.answers.filter_by(user_id=user_id).first()


class DailySelection(db.Model):
    """Pins one question per couple per calendar day (in the couple's own
    timezone) so both partners always see the *same* daily question, and so
    re-visiting the app doesn't roll a new one."""

    __tablename__ = "daily_selections"
    __table_args__ = (db.UniqueConstraint("couple_id", "date", name="uq_daily_couple_date"),)

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey("rounds.id"), nullable=False)

    round = db.relationship("Round")
