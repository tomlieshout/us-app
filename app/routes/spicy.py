from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.services.privacy import AccessDenied, get_owned_round, spicy_unlocked
from app.services.spicy import compute_matches

spicy_bp = Blueprint("spicy", __name__)


@spicy_bp.get("/matches")
@login_required
def matches():
    if not spicy_unlocked(current_user.couple):
        return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403
    return jsonify(compute_matches(current_user.couple))


@spicy_bp.post("/rounds/<int:round_id>/delete")
@login_required
def delete_spicy_round(round_id):
    """Either partner can permanently delete a spicy question's round and
    both answers - no confirmation from the other partner is required, by
    design, since this is about personal comfort with sensitive content."""
    try:
        round_ = get_owned_round(round_id, current_user)
    except AccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    if round_.question.category != "spicy":
        return jsonify({"error": "validation", "message": "This isn't a Spicy question."}), 400

    db.session.delete(round_)
    db.session.commit()
    return jsonify({"ok": True, "deleted_round_id": round_id})
