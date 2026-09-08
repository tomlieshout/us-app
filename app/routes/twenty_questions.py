from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services.twenty_questions import (
    TwentyQuestionsAccessDenied,
    TwentyQuestionsError,
    abandon_game,
    answer_question,
    ask_question,
    create_game,
    get_current_game,
    get_owned_game,
    serialize_game,
)

twenty_questions_bp = Blueprint("twenty_questions", __name__)


@twenty_questions_bp.get("/current")
@login_required
def current_game():
    game = get_current_game(current_user.couple)
    if game is None:
        return jsonify({"error": "no_game", "message": "No game yet - pick a secret to start one."}), 404
    return jsonify(serialize_game(game, current_user))


@twenty_questions_bp.get("/<int:game_id>")
@login_required
def get_game(game_id):
    try:
        game = get_owned_game(game_id, current_user)
    except TwentyQuestionsAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    return jsonify(serialize_game(game, current_user))


@twenty_questions_bp.post("/create")
@login_required
def create():
    data = request.get_json(silent=True) or {}
    try:
        game = create_game(current_user.couple, current_user, data.get("category"), data.get("secret_text"))
    except TwentyQuestionsError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400
    return jsonify(serialize_game(game, current_user)), 201


@twenty_questions_bp.post("/<int:game_id>/ask")
@login_required
def ask(game_id):
    try:
        game = get_owned_game(game_id, current_user)
    except TwentyQuestionsAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    data = request.get_json(silent=True) or {}
    try:
        ask_question(game, current_user, data.get("question_text"), is_guess=bool(data.get("is_guess")))
    except TwentyQuestionsError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400

    return jsonify(serialize_game(game, current_user)), 201


@twenty_questions_bp.post("/<int:game_id>/answer")
@login_required
def answer(game_id):
    try:
        game = get_owned_game(game_id, current_user)
    except TwentyQuestionsAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    data = request.get_json(silent=True) or {}
    try:
        answer_question(game, current_user, data.get("answer"))
    except TwentyQuestionsError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400

    return jsonify(serialize_game(game, current_user))


@twenty_questions_bp.post("/<int:game_id>/abandon")
@login_required
def abandon(game_id):
    try:
        game = get_owned_game(game_id, current_user)
    except TwentyQuestionsAccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    try:
        abandon_game(game, current_user)
    except TwentyQuestionsError as e:
        return jsonify({"error": "validation", "message": str(e)}), 400

    return jsonify(serialize_game(game, current_user))
