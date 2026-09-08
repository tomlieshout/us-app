from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.appreciation import (
    AppreciationAccessDenied,
    AppreciationError,
    delete_appreciation,
    get_owned_appreciation,
    list_received,
    list_sent,
    mark_seen,
    react,
    remove_reaction,
    send_appreciation,
    serialize_appreciation,
    toggle_keep,
    unseen_count,
)

appreciation_bp = Blueprint("appreciation", __name__)


@appreciation_bp.post("/send")
@login_required
def send():
    data = request.get_json(silent=True) or {}
    try:
        appreciation = send_appreciation(current_user.couple, current_user, data.get("message_text"))
    except AppreciationError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400
    return jsonify(serialize_appreciation(appreciation, current_user)), 201


@appreciation_bp.get("/received")
@login_required
def received():
    unseen_only = request.args.get("unseen_only") == "true"
    items = list_received(current_user, unseen_only=unseen_only)
    return jsonify({"appreciations": [serialize_appreciation(a, current_user) for a in items]})


@appreciation_bp.get("/sent")
@login_required
def sent():
    items = list_sent(current_user)
    return jsonify({"appreciations": [serialize_appreciation(a, current_user) for a in items]})


@appreciation_bp.get("/unseen-count")
@login_required
def unseen():
    return jsonify({"unseen_count": unseen_count(current_user)})


@appreciation_bp.post("/<int:appreciation_id>/seen")
@login_required
def seen(appreciation_id):
    try:
        appreciation = get_owned_appreciation(appreciation_id, current_user)
        mark_seen(appreciation, current_user)
    except AppreciationAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    except AppreciationError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400
    return jsonify(serialize_appreciation(appreciation, current_user))


@appreciation_bp.post("/<int:appreciation_id>/react")
@login_required
def add_reaction(appreciation_id):
    data = request.get_json(silent=True) or {}
    try:
        appreciation = get_owned_appreciation(appreciation_id, current_user)
        react(appreciation, current_user, data.get("reaction_type"))
    except AppreciationAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    except AppreciationError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400
    return jsonify(serialize_appreciation(appreciation, current_user))


@appreciation_bp.delete("/<int:appreciation_id>/react")
@login_required
def delete_reaction(appreciation_id):
    try:
        appreciation = get_owned_appreciation(appreciation_id, current_user)
        remove_reaction(appreciation, current_user)
    except AppreciationAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    except AppreciationError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400
    return jsonify(serialize_appreciation(appreciation, current_user))


@appreciation_bp.post("/<int:appreciation_id>/keep")
@login_required
def keep(appreciation_id):
    try:
        appreciation = get_owned_appreciation(appreciation_id, current_user)
        toggle_keep(appreciation, current_user)
    except AppreciationAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    except AppreciationError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400
    return jsonify(serialize_appreciation(appreciation, current_user))


@appreciation_bp.post("/<int:appreciation_id>/delete")
@login_required
def delete(appreciation_id):
    try:
        appreciation = get_owned_appreciation(appreciation_id, current_user)
        delete_appreciation(appreciation, current_user)
    except AppreciationAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    except AppreciationError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400
    return jsonify({"ok": True, "deleted_id": appreciation_id})
