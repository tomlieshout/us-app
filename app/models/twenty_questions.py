"""
20 Questions - a genuinely turn-based, asymmetric game (one chooser, one
guesser, strict alternating turns) that does not fit the Activity
architecture's "everyone submits once, then reveal together" shape at
all. This was flagged as needing its own structure back in the original
architecture audit, and confirmed explicitly rather than forced into
Activity/ActivityContent/ActivitySubmission/ActivityResult.

Two small tables, entirely separate from the activity_* tables:

    TwentyQuestionsGame   one couple's play-through: who chose, who's
                          guessing, the hidden secret, and how it ended.
    TwentyQuestionsTurn   one question-and-answer pair, numbered 1..20.
                          Turn order (ask -> answer -> next ask) is
                          enforced in app/services/twenty_questions.py,
                          not here - this model just stores the data.
"""

from datetime import datetime

from app.extensions import db

SECRET_CATEGORIES = ["person", "place", "thing"]
MAX_TURNS = 20


class TwentyQuestionsGame(db.Model):
    __tablename__ = "twenty_questions_games"

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey("couples.id"), nullable=False, index=True)

    chooser_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    guesser_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Category is shown to the guesser from the start (the classic game's
    # usual "I'm thinking of a person" hint) - only secret_text is hidden.
    secret_category = db.Column(db.String(16), nullable=False)
    secret_text = db.Column(db.String(200), nullable=False)

    # in_progress | won | lost | abandoned
    status = db.Column(db.String(16), nullable=False, default="in_progress", index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    couple = db.relationship("Couple", backref=db.backref("twenty_questions_games", lazy="dynamic"))
    chooser = db.relationship("User", foreign_keys=[chooser_user_id])
    guesser = db.relationship("User", foreign_keys=[guesser_user_id])
    turns = db.relationship(
        "TwentyQuestionsTurn",
        back_populates="game",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    @property
    def is_complete(self):
        return self.status != "in_progress"


class TwentyQuestionsTurn(db.Model):
    __tablename__ = "twenty_questions_turns"
    __table_args__ = (db.UniqueConstraint("game_id", "turn_number", name="uq_20q_game_turn_number"),)

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("twenty_questions_games.id"), nullable=False, index=True)
    turn_number = db.Column(db.Integer, nullable=False)

    question_text = db.Column(db.String(300), nullable=False)

    # A "guess" turn is the guesser directly naming what they think the
    # secret is, rather than a narrowing yes/no question. The chooser
    # answers it with correct/incorrect instead of yes/no (see `answer`).
    is_guess = db.Column(db.Boolean, nullable=False, default=False)

    # "yes"/"no" for a regular question, "correct"/"incorrect" for a
    # guess turn. Null until the chooser answers.
    answer = db.Column(db.String(16), nullable=True)

    asked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    answered_at = db.Column(db.DateTime, nullable=True)

    game = db.relationship("TwentyQuestionsGame", back_populates="turns")
