from datetime import datetime

from app.extensions import db


class Memory(db.Model):
    """A shared, manually-created memory: title, optional date, optional
    description, optional tags. Either partner can create/edit/delete;
    visibility is always scoped to the couple (see routes/memories.py)."""

    __tablename__ = "memories"

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, nullable=False, default=list)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    couple = db.relationship("Couple")
    created_by = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "description": self.description,
            "tags": self.tags or [],
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by.name if self.created_by else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
