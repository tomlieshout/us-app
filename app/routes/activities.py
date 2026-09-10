"""
Routes for the Activity system: daily/random/browse-play content
selection, submitting a response, viewing current state, and history.
This is now the live engine behind the app's main question/answer loop
(see app/static/js/views/*.js, which call these instead of the legacy
/api/rounds/*, /api/answers endpoints as of the architectural-integration
phase). The legacy routes are untouched and still fully functional -
Reactions, Comments, Spicy match-aggregation, and Stats still read the
legacy tables and have not been ported to the new engine yet (flagged as
a follow-up, not silently dropped).

Spicy visibility policy, enforced consistently across every route below:
while locked (spicy_unlocked() is False for the couple), Spicy content is
treated as if it does not exist anywhere - not served as new content, not
included in "All" history, and not directly viewable/submittable even via
a specific activity_id the user already has. Once both partners unlock it,
Spicy behaves as a normal category with no special-casing.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import ActivityContent
from app.services.activities import ActivityValidationError, DuplicateSubmissionError, get_handler
from app.services.activity_privacy import ActivityAccessDenied, get_owned_activity, serialize_activity
from app.services.activity_questions import (
    create_random_activity,
    get_or_create_activity_for_content,
    get_or_create_daily_activity,
)
from app.services.privacy import spicy_unlocked

activities_bp = Blueprint("activities", __name__)


def _is_hidden_spicy(activity):
    """True if this activity's content is Spicy and the couple currently
    has Spicy locked - i.e. it should be treated as if it doesn't exist,
    regardless of whether it was created/answered while unlocked."""
    return activity.content.category == "spicy" and not spicy_unlocked(activity.couple)


@activities_bp.get("/current")
@login_required
def current_activity():
    """Today's shared daily activity - the Activity-system counterpart to
    GET /api/rounds/current."""
    activity = get_or_create_daily_activity(current_user.couple, spicy_unlocked_flag=spicy_unlocked(current_user.couple))
    if activity is None:
        return jsonify({"error": "no_content", "message": "No content is available right now."}), 404
    if _is_hidden_spicy(activity):
        # Rare edge case: today's daily was selected earlier while Spicy
        # was unlocked, then someone disabled it later the same day. Treat
        # it the same as "nothing available" rather than exposing it.
        return jsonify({"error": "no_content", "message": "No content is available right now."}), 404
    return jsonify(serialize_activity(activity, current_user))


@activities_bp.get("/random")
@login_required
def random_activity():
    category = request.args.get("category")
    activity_type = request.args.get("activity_type", "classic_question")
    if category == "spicy" and not spicy_unlocked(current_user.couple):
        return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403

    activity = create_random_activity(
        current_user.couple, category=category, activity_type=activity_type,
        spicy_unlocked_flag=spicy_unlocked(current_user.couple),
    )
    if activity is None:
        return jsonify({"error": "no_content", "message": "No more content in that category right now."}), 404
    return jsonify(serialize_activity(activity, current_user))


@activities_bp.post("/play/<int:question_id>")
@login_required
def play_legacy_question(question_id):
    """Browse screen entry point: takes a *legacy Question id* (the
    browsing catalog at /api/questions is unchanged and still keyed by
    Question, since content browsing is identical data either way - see
    routes/questions.py), resolves it to the matching migrated
    ActivityContent, and creates/reuses an Activity for it. This is what
    lets the existing Browse UI keep working unchanged while the actual
    play/answer/reveal goes through the new engine."""
    content = (
        ActivityContent.query.filter_by(activity_type="classic_question", active=True)
        .all()
    )
    match = next((c for c in content if c.payload.get("legacy_question_id") == question_id), None)
    if match is None:
        return jsonify({"error": "not_found", "message": "That question isn't available."}), 404

    if match.category == "spicy" and not spicy_unlocked(current_user.couple):
        return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403

    activity = get_or_create_activity_for_content(current_user.couple, match)
    return jsonify(serialize_activity(activity, current_user)), 201


@activities_bp.get("/history")
@login_required
def activity_history():
    """Memories/History page - the Activity-system counterpart to
    GET /api/rounds/history.

    Spicy is fully hidden from the "All" view while locked - not just
    gated from new access, but excluded from a couple's own past history
    too, per the module-level Spicy visibility policy. Once unlocked,
    Spicy behaves as a normal category and is included in "All" like
    everything else. Explicitly requesting the "spicy" filter still
    requires spicy_unlocked()."""
    from app.models import Activity

    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(int(request.args.get("per_page", 20)), 50)
    category = request.args.get("category")

    query = current_user.couple.activities.filter(Activity.revealed_at.isnot(None))
    if category:
        if category == "spicy" and not spicy_unlocked(current_user.couple):
            return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403
        query = query.join(ActivityContent).filter(ActivityContent.category == category)
    elif not spicy_unlocked(current_user.couple):
        query = query.join(ActivityContent).filter(
            db.or_(ActivityContent.category.is_(None), ActivityContent.category != "spicy")
        )
    # else: unlocked and no category filter - include everything, Spicy included.

    total = query.count()
    activities = (
        query.order_by(Activity.revealed_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    )

    return jsonify(
        {
            "activities": [serialize_activity(a, current_user) for a in activities],
            "page": page,
            "per_page": per_page,
            "total": total,
            "has_more": page * per_page < total,
        }
    )


@activities_bp.get("/<int:activity_id>")
@login_required
def get_activity(activity_id):
    try:
        activity = get_owned_activity(activity_id, current_user)
    except ActivityAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    if _is_hidden_spicy(activity):
        # Same rule as everywhere else: while locked, treat a Spicy
        # activity as if it doesn't exist, even via a direct ID the user
        # already has (e.g. a bookmarked link, or a history entry loaded
        # just before Spicy was disabled).
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    return jsonify(serialize_activity(activity, current_user))


@activities_bp.post("/<int:activity_id>/submit")
@login_required
def submit_activity(activity_id):
    try:
        activity = get_owned_activity(activity_id, current_user)
    except ActivityAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    if _is_hidden_spicy(activity):
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    data = request.get_json(silent=True) or {}
    handler = get_handler(activity.content.activity_type)

    try:
        handler.submit(activity, current_user, data)
    except DuplicateSubmissionError as e:
        return jsonify({"error": "duplicate_submission", "message": str(e)}), 400
    except ActivityValidationError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400

    # Attempting reveal after every submission is a no-op (returns None,
    # changes nothing) unless this submission was the one that completed
    # the activity - identical timing to the legacy submit_answer route.
    handler.reveal(activity)

    return jsonify(serialize_activity(activity, current_user)), 201
