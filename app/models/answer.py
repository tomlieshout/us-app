from datetime import datetime

from app.extensions import db


class Answer(db.Model):
    __tablename__ = "answers"
    __table_args__ = (db.UniqueConstraint("round_id", "user_id", name="uq_answer_round_user"),)

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey("rounds.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Free-text answer, or the human-readable label for a chosen option.
    answer_text = db.Column(db.Text, nullable=True)

    # The exact option string chosen, for multiple_choice / rating /
    # structured_scale questions. Kept separate from answer_text so scoring
    # and match-aggregation can compare exact values.
    answer_option = db.Column(db.String(120), nullable=True)

    # Only used on "know_me" prediction questions: this user's guess at what
    # their partner will answer (compared against the partner's own
    # answer_option once both are in).
    predicted_option = db.Column(db.String(120), nullable=True)

    # "Keep this answer private" - mainly used for Spicy questions. When
    # true, the partner is told an answer exists but never its content.
    is_private = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    round = db.relationship("Round", back_populates="answers")
    user = db.relationship("User", back_populates="answers")
    reactions = db.relationship("Reaction", back_populates="answer", lazy="dynamic", cascade="all, delete-orphan")

    def public_value(self):
        """The value shown once both partners have answered and it's not
        marked private."""
        return self.answer_text if self.answer_text is not None else self.answer_option
