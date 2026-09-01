from datetime import datetime

from app.extensions import db


class Favourite(db.Model):
    __tablename__ = "favourites"
    __table_args__ = (db.UniqueConstraint("user_id", "question_id", name="uq_favourite_user_question"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    question = db.relationship("Question")
