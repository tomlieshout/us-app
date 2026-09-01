from datetime import datetime

from app.extensions import db

REACTION_TYPES = ["love", "funny", "cute", "surprised"]
REACTION_EMOJI = {"love": "❤️", "funny": "😂", "cute": "🥹", "surprised": "😮"}


class Reaction(db.Model):
    __tablename__ = "reactions"
    __table_args__ = (db.UniqueConstraint("answer_id", "user_id", name="uq_reaction_answer_user"),)

    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey("answers.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    reaction_type = db.Column(db.String(16), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    answer = db.relationship("Answer", back_populates="reactions")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "answer_id": self.answer_id,
            "user_id": self.user_id,
            "reaction_type": self.reaction_type,
            "emoji": REACTION_EMOJI.get(self.reaction_type, ""),
        }
