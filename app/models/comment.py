from datetime import datetime

from app.extensions import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey("rounds.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    comment_text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    round = db.relationship("Round", back_populates="comments")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "round_id": self.round_id,
            "user_id": self.user_id,
            "user_name": self.user.name,
            "comment_text": self.comment_text,
            "created_at": self.created_at.isoformat() + "Z",
        }
