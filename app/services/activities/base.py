"""
The reusable activity service interface. Every activity_type (starting
with "classic_question", more to follow later) implements this by
subclassing ActivityHandler and registering itself in registry.py.

Design split:
  - submit(), is_complete(), and reveal() have correct, generic default
    implementations here, reusable as-is by most future symmetric
    "everybody submits once, then reveal" game types.
  - validate_payload() and compute_result() are the two things that are
    always type-specific, and are the only two a subclass MUST implement.

This mirrors, deliberately, how legacy answers.py / privacy.py split
"generic mechanics" from "type-specific validation" - just made explicit
and reusable across activity_types instead of living inline in one route.
"""

from datetime import datetime

from app.extensions import db
from app.models import ActivityResult, ActivitySubmission


class ActivityValidationError(Exception):
    """The submitted payload doesn't fit what this activity_type expects."""


class DuplicateSubmissionError(Exception):
    """This user already submitted for this activity - submissions are not
    editable once locked in, matching the legacy Answer convention."""


class ActivityHandler:
    activity_type = None  # subclasses set this; must match ActivityContent.activity_type

    # ---- type-specific: every subclass must implement these two ----

    def validate_payload(self, activity, raw_payload):
        """Validate `raw_payload` (the client's JSON body) against
        `activity.content` (never against client-declared assumptions -
        always re-check against the DB-loaded content, same rule as
        legacy _validate_answer_payload). Returns a normalized dict to be
        stored as the submission's payload, or raises ActivityValidationError."""
        raise NotImplementedError

    def compute_result(self, activity):
        """Pure computation over a *complete* activity's submissions.
        Must NOT read any client-supplied score/points/outcome - only the
        already-validated, already-persisted submission payloads. Returns:
            {
              "is_competitive": bool,
              "outcome": str | None,
              "points": {"<user_id>": int, ...},
              "payload": {...},   # anything else type-specific
            }
        Does not persist anything - reveal() does that."""
        raise NotImplementedError

    def redact_content_payload(self, content, activity, viewer, revealed):
        """Most games' ActivityContent has nothing to hide - the options
        in a multiple-choice question aren't secret, so the default here
        is a no-op. Override this when a game's *content itself* embeds
        something that must stay hidden until reveal (e.g. Emoji Story's
        pre-written intended explanation, or a partner-authored story's
        explanation before the guess comes in) - the secret in that case
        isn't in a submission at all, so serialize_activity's usual
        submission-privacy logic has nothing to gate on without this
        hook."""
        return content.payload

    # ---- generic: reusable defaults, override only if a game genuinely
    # needs different mechanics (e.g. a future turn-based game) ----

    def is_complete(self, activity):
        members = activity.couple.ordered_members()
        if len(members) != 2:
            return False
        return all(activity.submission_for(m.id) is not None for m in members)

    def submit(self, activity, user, raw_payload):
        if activity.submission_for(user.id) is not None:
            raise DuplicateSubmissionError("You've already submitted for this activity.")

        normalized = self.validate_payload(activity, raw_payload)

        # Same restriction as the legacy system: "keep private" only
        # actually takes effect for Spicy content, regardless of what the
        # client sends.
        is_private = bool(raw_payload.get("is_private")) and activity.content.category == "spicy"

        submission = ActivitySubmission(
            activity_id=activity.id,
            user_id=user.id,
            is_private=is_private,
        )
        submission.payload = normalized
        db.session.add(submission)
        db.session.commit()
        return submission

    def reveal(self, activity):
        """Idempotent: if already revealed/resulted, returns the existing
        result without recomputing. If not yet complete, returns None
        without side effects - this is safe to call after every submit()."""
        if activity.result is not None:
            return activity.result
        if not self.is_complete(activity):
            return None

        computed = self.compute_result(activity)

        result = ActivityResult(
            activity_id=activity.id,
            is_competitive=bool(computed.get("is_competitive", False)),
            outcome=computed.get("outcome"),
        )
        result.points = computed.get("points", {})
        result.payload = computed.get("payload", {})
        db.session.add(result)

        if activity.revealed_at is None:
            activity.revealed_at = datetime.utcnow()

        db.session.commit()
        return result
