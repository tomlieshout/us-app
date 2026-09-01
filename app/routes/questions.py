from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.models import Favourite, Question
from app.services.privacy import spicy_unlocked
from app.services.questions import get_or_create_round_for_question

questions_bp = Blueprint("questions", __name__)

CATEGORY_META = [
    {"key": "relationship", "label": "Relationship", "emoji": "❤️", "description": "About us, together."},
    {"key": "know_me", "label": "How Well Do You Know Me?", "emoji": "🧠", "description": "Guess each other's answers."},
    {"key": "future", "label": "Future", "emoji": "🔮", "description": "Plans, dreams, what's next."},
    {"key": "random", "label": "Random / Funny", "emoji": "😂", "description": "Lighthearted and silly."},
    {"key": "deep", "label": "Deep", "emoji": "💭", "description": "More meaningful questions."},
    {"key": "memories", "label": "Memories", "emoji": "📸", "description": "Shared experiences."},
    {"key": "longdistance", "label": "Long Distance", "emoji": "🌍", "description": "Made for when you're apart."},
    {
        "key": "spicy",
        "label": "Spicy",
        "emoji": "🔥",
        "description": "Intimate topics. Opt-in for both of you.",
        "optional": True,
    },
]


@questions_bp.get("/categories")
@login_required
def categories():
    unlocked = spicy_unlocked(current_user.couple)
    out = []
    for c in CATEGORY_META:
        entry = dict(c)
        if c["key"] == "spicy":
            entry["locked"] = not unlocked
        out.append(entry)
    return jsonify({"categories": out})


@questions_bp.get("")
@login_required
def list_questions():
    category = request.args.get("category")
    if category == "spicy" and not spicy_unlocked(current_user.couple):
        return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403

    query = Question.query.filter_by(active=True)
    if category:
        query = query.filter_by(category=category)
    else:
        query = query.filter(Question.category != "spicy")

    questions = query.order_by(Question.id.asc()).all()

    favourite_ids = {
        f.question_id for f in Favourite.query.filter_by(user_id=current_user.id).all()
    }
    played_ids = {r.question_id for r in current_user.couple.rounds}

    return jsonify(
        {
            "questions": [
                {
                    **q.to_dict(),
                    "is_favourite": q.id in favourite_ids,
                    "already_played": q.id in played_ids,
                }
                for q in questions
            ]
        }
    )


@questions_bp.post("/<int:question_id>/play")
@login_required
def play_question(question_id):
    """Browse screen: the user picked a specific question to answer now."""
    question = Question.query.get(question_id)
    if not question or not question.active:
        return jsonify({"error": "not_found", "message": "That question isn't available."}), 404

    if question.category == "spicy" and not spicy_unlocked(current_user.couple):
        return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403

    round_ = get_or_create_round_for_question(current_user.couple, question)
    from app.services.privacy import serialize_round

    return jsonify(serialize_round(round_, current_user)), 201
