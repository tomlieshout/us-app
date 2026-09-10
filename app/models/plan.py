from datetime import datetime

from app.extensions import db


class Plan(db.Model):
    """A single reusable model for everything on the Plans page - Movies &
    Shows, Dates, Holidays, Trips, Things To Do, and Wishlist are all just
    different `category` values on the same table (per the brief: "Do NOT
    create six separate database tables"), the same way ActivityContent uses
    one table for every question type instead of one table per game.

    Visibility: a Plan belongs to the couple and is visible to both partners
    by default. `is_private` narrows that to the creator only - see
    to_dict()'s redaction, which follows the same "never query/serialize the
    sensitive fields for a non-owner" rule as services/privacy.py's
    _answer_view. A private item's *existence* still shows up in listings
    (so browsing a shared category doesn't have silently-missing rows), but
    its title/notes are never present in the JSON for anyone but the owner.
    """

    __tablename__ = "plans"

    # (key, label) - key is what's stored/validated against; label is
    # display-only, mirrored in the /api/plans/categories and /statuses
    # endpoints so the frontend never hardcodes its own copy of this list.
    CATEGORIES = [
        ("movies_shows", "Movies & Shows"),
        ("dates", "Dates"),
        ("holidays", "Holidays"),
        ("trips", "Trips"),
        ("things_to_do", "Things To Do"),
        ("wishlist", "Wishlist"),
    ]
    CATEGORY_KEYS = [key for key, _ in CATEGORIES]

    # Order matters here - it's the natural someday -> done progression, and
    # the frontend uses this order for the status picker.
    STATUSES = [
        ("someday", "Someday"),
        ("want_to_do", "Want to do"),
        ("planned", "Planned"),
        ("done", "Done"),
    ]
    STATUS_KEYS = [key for key, _ in STATUSES]

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    added_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(32), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, default="someday", index=True)
    notes = db.Column(db.Text, nullable=True)
    is_private = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    couple = db.relationship("Couple")
    added_by = db.relationship("User")

    def to_dict(self, viewer=None):
        is_owner = viewer is not None and viewer.id == self.added_by_id

        base = {
            "id": self.id,
            "category": self.category,
            "status": self.status,
            "is_private": self.is_private,
            "added_by_id": self.added_by_id,
            "added_by_name": self.added_by.name if self.added_by else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if self.is_private and not is_owner:
            base["hidden"] = True
            return base

        base["title"] = self.title
        base["notes"] = self.notes
        return base
