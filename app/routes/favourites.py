from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Favourite, Question
from app.services.privacy import spicy_unlocked

favourites_bp = Blueprint("favourites", __name__)


@favourites_bp.get("")
@login_required
def list_favourites():
    unlocked = spicy_unlocked(current_user.couple)
    favs = (
        Favourite.query.filter_by(user_id=current_user.id)
        .join(Question)
        .filter(Question.active.is_(True))
        .order_by(Favourite.created_at.desc())
        .all()
    )
    out = []
    for f in favs:
        if f.question.category == "spicy" and not unlocked:
            continue
        out.append(f.question.to_dict())
    return jsonify({"favourites": out})


@favourites_bp.post("")
@login_required
def add_favourite():
    data = request.get_json(silent=True) or {}
    question_id = data.get("question_id")
    question = Question.query.get(question_id) if question_id else None
    if not question:
        return jsonify({"error": "not_found", "message": "That question couldn't be found."}), 404

    existing = Favourite.query.filter_by(user_id=current_user.id, question_id=question.id).first()
    if not existing:
        db.session.add(Favourite(user_id=current_user.id, question_id=question.id))
        db.session.commit()
    return jsonify({"ok": True, "question_id": question.id}), 201


@favourites_bp.delete("/<int:question_id>")
@login_required
def remove_favourite(question_id):
    existing = Favourite.query.filter_by(user_id=current_user.id, question_id=question_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    return jsonify({"ok": True, "question_id": question_id})
