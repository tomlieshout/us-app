from datetime import datetime

from flask_login import UserMixin

from app.extensions import db, bcrypt


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)

    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)

    avatar_color = db.Column(db.String(16), nullable=False, default="#E85D75")
    dark_mode_pref = db.Column(db.String(10), nullable=False, default="system")  # system|light|dark

    # Spicy category requires each partner to independently opt in, and we
    # only allow that opt-in once the account holder has confirmed they are
    # an adult (see routes/settings.py).
    is_adult_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    spicy_opt_in = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    couple = db.relationship("Couple", back_populates="users")
    answers = db.relationship("Answer", back_populates="user", lazy="dynamic")

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_public_dict(self):
        """Safe to show to the user's partner."""
        return {
            "id": self.id,
            "name": self.name,
            "avatar_color": self.avatar_color,
        }

    def to_private_dict(self):
        """Only ever returned to the user themselves."""
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "email": self.email,
            "avatar_color": self.avatar_color,
            "dark_mode_pref": self.dark_mode_pref,
            "is_adult_confirmed": self.is_adult_confirmed,
            "spicy_opt_in": self.spicy_opt_in,
            "couple_id": self.couple_id,
        }
