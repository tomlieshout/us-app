import json
from datetime import datetime

from app.extensions import db

CATEGORIES = [
    "relationship",   # Relationship
    "know_me",        # How Well Do You Know Me? (prediction)
    "future",         # Future
    "random",         # Random / Funny
    "deep",           # Deep
    "memories",       # Memories
    "longdistance",   # Long-distance specific (surfaced inside relevant categories too)
    "spicy",          # Optional, opt-in, adults-only (see spicy_level)
]

QUESTION_TYPES = ["free_text", "multiple_choice", "rating", "prediction", "structured_scale"]

# Used for structured_scale questions (mainly Spicy "Intimate"/"Adventurous" tiers)
# so both partners answer from the same fixed vocabulary, which is what makes
# the mutual-match feature possible.
INTEREST_SCALE = ["Definitely interested", "Maybe / curious", "Not sure", "Probably not", "Definitely not"]


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    # For "know_me" prediction questions, `text` is phrased for the person
    # giving their own real answer (e.g. "What's your ideal holiday?").
    # `predict_text` is the phrasing shown to their partner, who is guessing
    # (e.g. "What would your partner choose for the perfect holiday?").
    predict_text = db.Column(db.Text, nullable=True)

    category = db.Column(db.String(32), nullable=False, index=True)
    question_type = db.Column(db.String(32), nullable=False, default="free_text")

    # JSON-encoded list of strings for multiple_choice / rating / structured_scale
    options_json = db.Column(db.Text, nullable=True)

    # Only set (1/2/3) for category == "spicy"
    spicy_level = db.Column(db.Integer, nullable=True)

    # Structured-scale spicy questions that are safe to fold into the
    # "Find your matches" aggregate view.
    match_eligible = db.Column(db.Boolean, nullable=False, default=False)

    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def options(self):
        if not self.options_json:
            return None
        return json.loads(self.options_json)

    @options.setter
    def options(self, value):
        self.options_json = json.dumps(value) if value is not None else None

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "predict_text": self.predict_text,
            "category": self.category,
            "question_type": self.question_type,
            "options": self.options,
            "spicy_level": self.spicy_level,
            "match_eligible": self.match_eligible,
        }
