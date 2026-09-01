from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Reaction
from app.models.reaction import REACTION_TYPES
from app.services.privacy import AccessDenied, get_owned_answer

reactions_bp = Blueprint("reactions", __name__)


@reactions_bp.post("")
@login_required
def add_reaction():
    data = request.get_json(silent=True) or {}
    answer_id = data.get("answer_id")
    reaction_type = data.get("reaction_type")

    if reaction_type not in REACTION_TYPES:
        return jsonify({"error": "validation", "message": "Unknown reaction type."}), 400

    try:
        answer = get_owned_answer(int(answer_id), current_user)
    except (AccessDenied, ValueError, TypeError):
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    if answer.user_id == current_user.id:
        return jsonify({"error": "validation", "message": "You can react to your partner's answer, not your own."}), 400

    existing = Reaction.query.filter_by(answer_id=answer.id, user_id=current_user.id).first()
    if existing:
        existing.reaction_type = reaction_type
    else:
        db.session.add(Reaction(answer_id=answer.id, user_id=current_user.id, reaction_type=reaction_type))
    db.session.commit()

    reactions = [r.to_dict() for r in answer.reactions]
    return jsonify({"answer_id": answer.id, "reactions": reactions}), 201


@reactions_bp.delete("/<int:answer_id>")
@login_required
def remove_reaction(answer_id):
    try:
        answer = get_owned_answer(answer_id, current_user)
    except AccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    existing = Reaction.query.filter_by(answer_id=answer.id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    reactions = [r.to_dict() for r in answer.reactions]
    return jsonify({"answer_id": answer.id, "reactions": reactions})
