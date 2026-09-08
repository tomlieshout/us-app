"""
Emoji Story: the first game where the secret lives in the CONTENT, not in
a submission - the intended explanation is written down (either by the
app's seed data, or by the creating partner) before anyone plays, so it
has to be redacted from serialize_activity's response rather than simply
never-queried like every other game's data. See
ActivityHandler.redact_content_payload and app/services/activity_privacy.py.

Two modes, both stored as activity_type="emoji_story", distinguished by
ActivityContent.category (reusing the existing category column/filtering
machinery rather than inventing a parallel concept):

    category="guess"            Mode 1 - app-provided. Seeded content, an
                                 emoji_sequence + a pre-written explanation.
                                 Solo: whoever plays it submits one guess
                                 and sees the reveal immediately - there is
                                 no partner submission to wait for.

    category="partner_created"  Mode 2 - one partner writes emoji_sequence
                                 + explanation (see app/routes/emoji_story.py
                                 for creation), the OTHER partner submits a
                                 guess. Reveal happens once the guesser (not
                                 the creator - the creator never submits
                                 anything to this Activity) has submitted.

No automatic semantic scoring, by design - this is a conversation game,
not a quiz. compute_result never awards points.
"""

from app.services.activities.base import ActivityHandler, ActivityValidationError

MAX_GUESS_LENGTH = 500


class EmojiStoryActivity(ActivityHandler):
    activity_type = "emoji_story"

    def validate_payload(self, activity, raw_payload):
        guess = (raw_payload.get("guess") or "").strip()
        if not guess:
            raise ActivityValidationError("Write your guess for what the story means.")
        if len(guess) > MAX_GUESS_LENGTH:
            raise ActivityValidationError("That's a bit long - keep it under 500 characters.")
        return {"guess": guess}

    def submit(self, activity, user, raw_payload):
        creator_id = activity.content.payload.get("created_by_user_id")
        if activity.content.category == "partner_created" and creator_id == user.id:
            # Defensive: a creator should never be able to reach their own
            # story's Activity id and guess it themselves, even though the
            # normal /guess picker already excludes their own creations.
            raise ActivityValidationError("You can't guess your own story.")
        return super().submit(activity, user, raw_payload)

    def is_complete(self, activity):
        mode = activity.content.category
        if mode == "guess":
            # Solo: reveal as soon as the one player has guessed - there's
            # no partner submission to wait for in this mode.
            return activity.submissions.count() >= 1
        if mode == "partner_created":
            creator_id = activity.content.payload.get("created_by_user_id")
            return any(s.user_id != creator_id for s in activity.submissions.all())
        return super().is_complete(activity)

    def redact_content_payload(self, content, activity, viewer, revealed):
        payload = dict(content.payload)
        is_creator = content.category == "partner_created" and payload.get("created_by_user_id") == viewer.id
        if not revealed and not is_creator:
            payload.pop("explanation", None)
        return payload

    def compute_result(self, activity):
        # Deliberately no scoring of any kind - see module docstring.
        return {"is_competitive": False, "outcome": None, "points": {}, "payload": {}}
