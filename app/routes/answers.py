from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Answer
from app.services.privacy import AccessDenied, get_owned_round, serialize_round

answers_bp = Blueprint("answers", __name__)

MAX_TEXT_LENGTH = 2000


def _validate_answer_payload(question, data):
    """Returns (answer_text, answer_option, predicted_option) or raises a
    (message, status_code) tuple via ValueError-style return of an error
    dict. All validation happens server-side - the client's declared
    question_type is never trusted, `question` (loaded from the DB) is."""
    qtype = question.question_type
    options = question.options or []

    if qtype == "free_text":
        text = (data.get("answer_text") or "").strip()
        if not text:
            return None, {"error": "validation", "message": "Please write an answer."}
        if len(text) > MAX_TEXT_LENGTH:
            return None, {"error": "validation", "message": "That answer is too long."}
        return {"answer_text": text, "answer_option": None, "predicted_option": None}, None

    if qtype in ("multiple_choice", "rating", "structured_scale"):
        option = data.get("answer_option")
        if option not in options:
            return None, {"error": "validation", "message": "Please choose one of the given options."}
        return {"answer_text": None, "answer_option": option, "predicted_option": None}, None

    if qtype == "prediction":
        option = data.get("answer_option")
        predicted = data.get("predicted_option")
        if option not in options:
            return None, {"error": "validation", "message": "Please choose your real answer."}
        if predicted not in options:
            return None, {"error": "validation", "message": "Please choose what you think your partner will say."}
        return {"answer_text": None, "answer_option": option, "predicted_option": predicted}, None

    return None, {"error": "validation", "message": "Unsupported question type."}


@answers_bp.post("")
@login_required
def submit_answer():
    data = request.get_json(silent=True) or {}
    round_id = data.get("round_id")
    if not round_id:
        return jsonify({"error": "validation", "message": "round_id is required."}), 400

    try:
        round_ = get_owned_round(int(round_id), current_user)
    except (AccessDenied, ValueError, TypeError):
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404

    if round_.answer_for(current_user.id) is not None:
        return jsonify({"error": "duplicate_answer", "message": "You've already answered this question."}), 400

    question = round_.question
    fields, error = _validate_answer_payload(question, data)
    if error:
        return jsonify(error), 400

    is_private = bool(data.get("is_private")) and question.category == "spicy"

    answer = Answer(
        round_id=round_.id,
        user_id=current_user.id,
        answer_text=fields["answer_text"],
        answer_option=fields["answer_option"],
        predicted_option=fields["predicted_option"],
        is_private=is_private,
    )
    db.session.add(answer)
    db.session.flush()

    # Reveal the instant both partners are in - this is the one place the
    # server is allowed to look at both answers at once.
    partner = round_.couple.other_member(current_user)
    if partner and round_.answer_for(partner.id) is not None and round_.revealed_at is None:
        round_.revealed_at = datetime.utcnow()

    db.session.commit()
    return jsonify(serialize_round(round_, current_user)), 201


@answers_bp.get("/status/<int:round_id>")
@login_required
def answer_status(round_id):
    """Kept as a thin alias so the API matches the brief's /answer/status
    naming; identical payload to GET /api/rounds/<id>."""
    try:
        round_ = get_owned_round(round_id, current_user)
    except AccessDenied:
        return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
    return jsonify(serialize_round(round_, current_user))
