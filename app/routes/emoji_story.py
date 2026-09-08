"""
Emoji Story-specific routes. Everything else about this game (submitting
a guess, viewing an activity's current/revealed state) reuses the generic
/api/activities/<id> and /api/activities/<id>/submit routes unchanged -
these three are only needed because Emoji Story's "partner-created" mode
involves creating brand-new ActivityContent at runtime (not from seed
data) and picking a partner-created story while excluding your own.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Activity, ActivityContent
from app.services.activity_privacy import serialize_activity
from app.services.activity_questions import get_or_create_activity_for_content, pick_content_for_couple

emoji_story_bp = Blueprint("emoji_story", __name__)

MAX_SEQUENCE_LENGTH = 40
MAX_EXPLANATION_LENGTH = 500


@emoji_story_bp.post("/create")
@login_required
def create_story():
    """Mode 2, step 1: write a story for your partner to guess later.
    No limit on how many a person can create."""
    data = request.get_json(silent=True) or {}
    emoji_sequence = (data.get("emoji_sequence") or "").strip()
    explanation = (data.get("explanation") or "").strip()

    if not emoji_sequence:
        return jsonify({"error": "validation", "message": "Add at least one emoji."}), 400
    if len(emoji_sequence) > MAX_SEQUENCE_LENGTH:
        return jsonify({"error": "validation", "message": "That's a lot of emoji - keep it shorter."}), 400
    if not explanation:
        return jsonify({"error": "validation", "message": "Write what it means - your partner won't see this until they guess."}), 400
    if len(explanation) > MAX_EXPLANATION_LENGTH:
        return jsonify({"error": "validation", "message": "That explanation is a bit long - keep it under 500 characters."}), 400

    content = ActivityContent(
        activity_type="emoji_story",
        category="partner_created",
        prompt="Your partner's emoji story",
        active=True,
    )
    content.payload = {
        "emoji_sequence": emoji_sequence,
        "explanation": explanation,
        "created_by_user_id": current_user.id,
    }
    db.session.add(content)
    db.session.commit()

    return jsonify({"content_id": content.id, "emoji_sequence": emoji_sequence}), 201


@emoji_story_bp.get("/mine")
@login_required
def my_stories():
    """List of stories I've created, with whatever guess (if any) has
    come in for each - lets a creator see the outcome without needing to
    know which Activity id, if any, got created for it."""
    my_content = [
        c
        for c in ActivityContent.query.filter_by(activity_type="emoji_story", category="partner_created").all()
        if c.payload.get("created_by_user_id") == current_user.id
    ]

    out = []
    for content in my_content:
        activity = (
            Activity.query.filter_by(content_id=content.id, couple_id=current_user.couple_id)
            .order_by(Activity.created_at.desc())
            .first()
        )
        entry = {
            "content_id": content.id,
            "emoji_sequence": content.payload.get("emoji_sequence"),
            "explanation": content.payload.get("explanation"),
            "guessed": False,
            "revealed": False,
            "guess": None,
        }
        if activity is not None:
            entry["activity_id"] = activity.id
            entry["revealed"] = activity.is_revealed
            guess_submission = next((s for s in activity.submissions.all() if s.user_id != current_user.id), None)
            if guess_submission is not None:
                entry["guessed"] = True
                entry["guess"] = guess_submission.payload.get("guess")
        out.append(entry)

    # Newest creations first.
    out.reverse()
    return jsonify({"stories": out})


@emoji_story_bp.post("/guess")
@login_required
def get_partner_story_to_guess():
    """Mode 2, step 2: fetch a partner-created story to guess - never
    your own, and preferring one you haven't already guessed."""
    content = pick_content_for_couple(
        current_user.couple,
        activity_type="emoji_story",
        category="partner_created",
        exclude_created_by_user_id=current_user.id,
    )
    if content is None:
        return jsonify({
            "error": "no_content",
            "message": "No stories from your partner yet - ask them to create one!",
        }), 404

    activity = get_or_create_activity_for_content(current_user.couple, content)
    return jsonify(serialize_activity(activity, current_user)), 201
