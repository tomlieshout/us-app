from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.challenges import (
    ChallengeAccessDenied,
    ChallengeError,
    accept_challenge,
    complete_challenge,
    get_owned_challenge,
    list_challenges,
    pick_challenge_for_couple,
    serialize_challenge,
)

challenges_bp = Blueprint("challenges", __name__)


@challenges_bp.get("/random")
@login_required
def random_challenge():
    category = request.args.get("category")
    try:
        content = pick_challenge_for_couple(current_user.couple, category=category)
    except ChallengeError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400

    if content is None:
        return jsonify({"error": "no_content", "message": "No challenges in that category right now."}), 404

    return jsonify(content.to_dict())


@challenges_bp.post("/accept")
@login_required
def accept():
    data = request.get_json(silent=True) or {}
    content_id = data.get("content_id")
    if not content_id:
        return jsonify({"error": "validation", "message": "content_id is required."}), 400

    try:
        challenge = accept_challenge(current_user.couple, content_id)
    except ChallengeError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400

    return jsonify(serialize_challenge(challenge, current_user)), 201


@challenges_bp.get("/mine")
@login_required
def mine():
    status = request.args.get("status")
    challenges = list_challenges(current_user.couple, status=status)
    return jsonify({"challenges": [serialize_challenge(c, current_user) for c in challenges]})


@challenges_bp.post("/<int:challenge_id>/complete")
@login_required
def complete(challenge_id):
    try:
        challenge = get_owned_challenge(challenge_id, current_user)
    except ChallengeAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    try:
        complete_challenge(challenge, current_user)
    except ChallengeError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400

    return jsonify(serialize_challenge(challenge, current_user))
