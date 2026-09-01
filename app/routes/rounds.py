from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.models import Question, Round
from app.services.privacy import AccessDenied, get_owned_round, serialize_round, spicy_unlocked
from app.services.questions import create_random_round, get_or_create_daily_round

rounds_bp = Blueprint("rounds", __name__)


@rounds_bp.get("/current")
@login_required
def current_round():
    """Today's shared daily question for the couple (created on first
    request each day, then stable for the rest of the day)."""
    round_ = get_or_create_daily_round(current_user.couple)
    if round_ is None:
        return jsonify({"error": "no_questions", "message": "No questions are available right now."}), 404
    return jsonify(serialize_round(round_, current_user))


@rounds_bp.get("/random")
@login_required
def random_round():
    category = request.args.get("category")
    if category == "spicy" and not spicy_unlocked(current_user.couple):
        return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403

    round_ = create_random_round(current_user.couple, category=category)
    if round_ is None:
        return jsonify({"error": "no_questions", "message": "No more questions in that category right now."}), 404
    return jsonify(serialize_round(round_, current_user))


@rounds_bp.get("/<int:round_id>")
@login_required
def round_status(round_id):
    try:
        round_ = get_owned_round(round_id, current_user)
    except AccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    return jsonify(serialize_round(round_, current_user))


@rounds_bp.get("/history")
@login_required
def history():
    """Memories page: previously completed (revealed) questions."""
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(int(request.args.get("per_page", 20)), 50)
    category = request.args.get("category")

    query = current_user.couple.rounds.filter(Round.revealed_at.isnot(None))
    if category:
        if category == "spicy" and not spicy_unlocked(current_user.couple):
            return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403
        query = query.join(Question).filter(Question.category == category)
    else:
        query = query.join(Question).filter(Question.category != "spicy")

    total = query.count()
    rounds = (
        query.order_by(Round.revealed_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return jsonify(
        {
            "rounds": [serialize_round(r, current_user) for r in rounds],
            "page": page,
            "per_page": per_page,
            "total": total,
            "has_more": page * per_page < total,
        }
    )
