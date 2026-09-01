from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Comment
from app.services.privacy import AccessDenied, get_owned_round

comments_bp = Blueprint("comments", __name__)

MAX_COMMENT_LENGTH = 500


@comments_bp.get("/<int:round_id>")
@login_required
def list_comments(round_id):
    try:
        round_ = get_owned_round(round_id, current_user)
    except AccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    if not round_.is_revealed:
        return jsonify({"comments": []})
    comments = round_.comments.order_by(Comment.created_at.asc()).all()
    return jsonify({"comments": [c.to_dict() for c in comments]})


@comments_bp.post("")
@login_required
def add_comment():
    data = request.get_json(silent=True) or {}
    round_id = data.get("round_id")
    text = (data.get("comment_text") or "").strip()

    if not text:
        return jsonify({"error": "validation", "message": "Comment can't be empty."}), 400
    if len(text) > MAX_COMMENT_LENGTH:
        return jsonify({"error": "validation", "message": "Comment is too long."}), 400

    try:
        round_ = get_owned_round(int(round_id), current_user)
    except (AccessDenied, ValueError, TypeError):
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    if not round_.is_revealed:
        return jsonify({"error": "not_revealed", "message": "You can comment once both answers are revealed."}), 400

    comment = Comment(round_id=round_.id, user_id=current_user.id, comment_text=text)
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.to_dict()), 201
