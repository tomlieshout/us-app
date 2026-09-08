"""
The reusable "Activity" system for Building Us game types.

This sits ALONGSIDE the original Question/Round/Answer system, which
continues to power the existing daily-question app untouched. Nothing here
reads or writes those tables, and nothing in the existing app reads or
writes these ones (yet).

Where Question/Round/Answer use one fixed column per concept (answer_text,
answer_option, predicted_option, ...), these models generalize that into a
single JSON payload per row, so a brand new activity_type - Would You
Rather, Who Would, a future game nobody's thought of yet - never requires a
new migration, only a new shape of dict.

    ActivityContent    the reusable prompt/template      (mirrors Question)
    Activity           one couple's instance of playing  (mirrors Round)
                        a piece of content
    ActivitySubmission one user's private response        (mirrors Answer)
    ActivityResult      optional computed outcome once revealed - match/no
                        match, prediction correctness, points awarded.
                        No equivalent exists in the original system (today's
                        prediction scoring is computed live in
                        services/prediction.py, nothing is persisted). This
                        is also the first piece of a competitive-scoring
                        ledger a future Stats view can sum across every
                        activity type from one place.
"""

import json
from datetime import datetime

from app.extensions import db

# Extended as new games are implemented. Deliberately a plain string column
# on ActivityContent below, not a DB enum, so adding a type is a data change
# rather than a migration - same reasoning as Question.category/question_type.
ACTIVITY_TYPES = ["question", "prediction", "would_you_rather"]


class ActivityContent(db.Model):
    __tablename__ = "activity_contents"

    id = db.Column(db.Integer, primary_key=True)

    # The game mechanic this content is played with - drives how the
    # frontend renders it and how `payload` below is shaped.
    activity_type = db.Column(db.String(32), nullable=False, index=True)

    # Optional thematic grouping (relationship / future / deep / spicy /
    # ...) - same free-text, non-FK convention as Question.category.
    category = db.Column(db.String(32), nullable=True, index=True)

    # The main display text: the question itself, the Would You Rather
    # framing line, etc.
    prompt = db.Column(db.Text, nullable=False)

    # Everything type-specific lives here instead of in more fixed columns.
    # Shape depends on activity_type, e.g.:
    #   question:          {"options": [...]}            (omitted -> free text)
    #   prediction:        {"options": [...], "predict_prompt": "..."}
    #   would_you_rather:  {"option_a": "...", "option_b": "..."}
    payload_json = db.Column(db.Text, nullable=True)

    # Same gating/aggregation columns as Question, ready for future Spicy
    # game variants (Spicy Prediction, Spicy Would You Rather, ...).
    spicy_level = db.Column(db.Integer, nullable=True)
    match_eligible = db.Column(db.Boolean, nullable=False, default=False)

    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def payload(self):
        if not self.payload_json:
            return {}
        return json.loads(self.payload_json)

    @payload.setter
    def payload(self, value):
        self.payload_json = json.dumps(value) if value is not None else None

    def to_dict(self):
        return {
            "id": self.id,
            "activity_type": self.activity_type,
            "category": self.category,
            "prompt": self.prompt,
            "payload": self.payload,
            "spicy_level": self.spicy_level,
            "match_eligible": self.match_eligible,
        }


class Activity(db.Model):
    """One couple's instance of playing a piece of ActivityContent - the
    generalized equivalent of Round."""

    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey("activity_contents.id"), nullable=False, index=True)

    is_daily = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Same "presence = revealed" convention as Round.revealed_at.
    revealed_at = db.Column(db.DateTime, nullable=True)

    # Free-form bucket for any per-activity runtime state a future game
    # needs (e.g. a turn counter for a sequential game) that isn't a
    # per-user submission. Unused by anything today - included so most
    # future game types won't need a schema change just to get started.
    state_json = db.Column(db.Text, nullable=True)

    # backref (not back_populates) deliberately, so this file is the only
    # one that needs to exist for the relationship to work - couple.py and
    # user.py are untouched.
    couple = db.relationship("Couple", backref=db.backref("activities", lazy="dynamic"))
    content = db.relationship("ActivityContent")
    submissions = db.relationship(
        "ActivitySubmission", back_populates="activity", lazy="dynamic", cascade="all, delete-orphan"
    )
    result = db.relationship("ActivityResult", back_populates="activity", uselist=False, cascade="all, delete-orphan")

    @property
    def is_revealed(self):
        return self.revealed_at is not None

    @property
    def state(self):
        if not self.state_json:
            return {}
        return json.loads(self.state_json)

    @state.setter
    def state(self, value):
        self.state_json = json.dumps(value) if value is not None else None

    def submission_for(self, user_id):
        return self.submissions.filter_by(user_id=user_id).first()


class ActivitySubmission(db.Model):
    """One user's private response to an Activity - the generalized
    equivalent of Answer. Unlike Answer (separate answer_text /
    answer_option / predicted_option columns), everything type-specific
    lives in one JSON payload, e.g.:
        question:          {"text": "Japan"}  or  {"option": "Beach"}
        prediction:        {"answer": "Beach", "predicted_partner": "Mountains"}
        would_you_rather:  {"choice": "a"}
    """

    __tablename__ = "activity_submissions"
    __table_args__ = (db.UniqueConstraint("activity_id", "user_id", name="uq_activity_submission_user"),)

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    payload_json = db.Column(db.Text, nullable=True)

    # Same "keep this private" convention as Answer.is_private - available
    # to any activity type, not just Spicy ones (that restriction, like
    # Answer's, is an application-layer rule, not a schema one).
    is_private = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    activity = db.relationship("Activity", back_populates="submissions")
    user = db.relationship("User", backref=db.backref("activity_submissions", lazy="dynamic"))

    @property
    def payload(self):
        if not self.payload_json:
            return {}
        return json.loads(self.payload_json)

    @payload.setter
    def payload(self, value):
        self.payload_json = json.dumps(value) if value is not None else None


class ActivityResult(db.Model):
    """Optional computed outcome for an Activity, written once (typically
    at reveal time): did they match, was the prediction correct, how many
    points did each partner earn.

    Nothing in the original system persists this - it's computed live on
    every request in services/prediction.py. This table exists so scoring
    can be looked up instead of recomputed, and so a future competitive
    Stats view can sum `points_json` across every activity type from one
    place instead of each game reinventing its own scoring query.
    """

    __tablename__ = "activity_results"

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False, unique=True, index=True)

    # Keeps the Building Us doc's "competitive score is separate" /
    # "no relationship score" rules enforceable with a single filter,
    # rather than a hardcoded list of which game names count.
    is_competitive = db.Column(db.Boolean, nullable=False, default=False)

    # Short, human-readable outcome label: "match", "no_match", "correct",
    # "incorrect", "draw", etc. Free string on purpose, not a fixed enum,
    # so a new outcome kind never needs a migration.
    outcome = db.Column(db.String(32), nullable=True)

    # {"<user_id>": <points:int>, ...} - a dict rather than two fixed
    # columns so it doesn't assume anything about member ordering, and a
    # draw (both get a point) or an asymmetric award is just as easy to
    # express as a single winner.
    points_json = db.Column(db.Text, nullable=True)

    # Anything else type-specific: an agreement percentage, explanatory
    # text, which option each side actually picked, etc.
    payload_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    activity = db.relationship("Activity", back_populates="result")

    @property
    def points(self):
        if not self.points_json:
            return {}
        return json.loads(self.points_json)

    @points.setter
    def points(self, value):
        self.points_json = json.dumps(value) if value is not None else None

    @property
    def payload(self):
        if not self.payload_json:
            return {}
        return json.loads(self.payload_json)

    @payload.setter
    def payload(self, value):
        self.payload_json = json.dumps(value) if value is not None else None


class ActivityDailySelection(db.Model):
    """Pins one Activity per couple per calendar day - the new system's
    counterpart to the legacy DailySelection, added during the
    architectural-integration phase so /api/activities/current can offer
    the same "same question all day, for both of you" guarantee. Separate
    table, same reasoning as DailySelection: inferring "today's activity"
    from a timestamp comparison alone is fragile across timezones; an
    explicit (couple_id, date) row is not."""

    __tablename__ = "activity_daily_selections"
    __table_args__ = (db.UniqueConstraint("couple_id", "date", name="uq_activity_daily_couple_date"),)

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey("activity_contents.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False)

    activity = db.relationship("Activity")
