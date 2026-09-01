import secrets
from datetime import datetime

from app.extensions import db


def _generate_invite_code(length=6):
    """A short, human-typeable, hard-to-guess code (no ambiguous chars)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no O/0, I/1 confusion
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Couple(db.Model):
    __tablename__ = "couples"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    invite_code = db.Column(db.String(16), unique=True, nullable=False, index=True)
    timezone = db.Column(db.String(64), nullable=False, default="UTC")
    accent_color = db.Column(db.String(16), nullable=False, default="#E85D75")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    users = db.relationship("User", back_populates="couple", lazy="dynamic")
    rounds = db.relationship("Round", back_populates="couple", lazy="dynamic")

    @staticmethod
    def make_unique_invite_code(length=6):
        for _ in range(50):
            code = _generate_invite_code(length)
            if not Couple.query.filter_by(invite_code=code).first():
                return code
        raise RuntimeError("Could not generate a unique invite code")

    @property
    def member_count(self):
        return self.users.count()

    def ordered_members(self):
        from app.models.user import User

        return self.users.order_by(User.id.asc()).all()

    def other_member(self, user):
        from app.models.user import User

        return self.users.filter(User.id != user.id).first()

    def display_name(self):
        if self.name:
            return self.name
        names = [m.name for m in self.ordered_members()]
        return " & ".join(names) if names else "Us"

    def to_dict(self):
        members = self.ordered_members()
        return {
            "id": self.id,
            "name": self.display_name(),
            "invite_code": self.invite_code if self.member_count < 2 else None,
            "timezone": self.timezone,
            "accent_color": self.accent_color,
            "members": [m.to_public_dict() for m in members],
            "is_complete": self.member_count >= 2,
            "spicy_unlocked": self.member_count >= 2 and all(m.spicy_opt_in for m in members),
        }
