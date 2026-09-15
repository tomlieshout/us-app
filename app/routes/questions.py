from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Activity, ActivityContent, ActivitySubmission, Favourite, Question
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


def _answered_question_ids_for(user_id):
    """Legacy Question ids this specific user has personally submitted an
    answer for, via the Activity system. Deliberately scoped to the one
    user, not the couple - the same per-user fix applied to random/toggle
    content selection (see activity_questions.pick_content_for_user):
    a question your partner answered isn't "already played" for you until
    you've actually answered it yourself."""
    content_ids = {
        row[0]
        for row in db.session.query(Activity.content_id)
        .join(ActivitySubmission, ActivitySubmission.activity_id == Activity.id)
        .filter(ActivitySubmission.user_id == user_id)
    }
    if not content_ids:
        return set()
    return {
        c.payload.get("legacy_question_id")
        for c in ActivityContent.query.filter(ActivityContent.id.in_(content_ids)).all()
        if c.payload.get("legacy_question_id") is not None
    }


@questions_bp.get("")
@login_required
def list_questions():
    category = request.args.get("category")
    unanswered_only = request.args.get("unanswered_only", "").lower() in ("1", "true", "yes")
    if category == "spicy" and not spicy_unlocked(current_user.couple):
        return jsonify({"error": "spicy_locked", "message": "Both partners need to opt in first."}), 403

    query = Question.query.filter_by(active=True)
    if category:
        query = query.filter_by(category=category)
    elif not spicy_unlocked(current_user.couple):
        query = query.filter(Question.category != "spicy")
    # else: no category filter and Spicy is unlocked - Spicy behaves as a
    # normal category, same as everywhere else in the app.

    # Level 1 before level 2 before level 3. Non-spicy questions have no
    # spicy_level (None), so coalesce() puts them all in one group of "0" -
    # this line is a no-op for every other category, only Spicy is
    # affected. Within a level, func.random() re-shuffles on every single
    # request (SQLite and Postgres both support RANDOM() natively), so
    # insertion order - i.e. what order they were seeded in - can never
    # cause bunching again, regardless of how future questions get added.
    questions = query.order_by(
        func.coalesce(Question.spicy_level, 0).asc(), func.random()
    ).all()

    favourite_ids = {
        f.question_id for f in Favourite.query.filter_by(user_id=current_user.id).all()
    }
    answered_question_ids = _answered_question_ids_for(current_user.id)

    result = [
        {
            **q.to_dict(),
            "is_favourite": q.id in favourite_ids,
            "already_played": q.id in answered_question_ids,
        }
        for q in questions
    ]
    if unanswered_only:
        result = [q for q in result if not q["already_played"]]

    return jsonify({"questions": result})


@questions_bp.get("/partner-answered")
@login_required
def partner_answered_questions():
    """Discovery entry point (Browse tab "Partner Answered" card): legacy
    Questions the couple currently has a pending (unrevealed) Activity for,
    where the partner has submitted and the current user hasn't - same
    underlying "pending from partner" concept as the WYR/KEO/WW toggle's
    mode=partner_pending and the general History page's view=partner, just
    surfaced here as Question rows so it can render like a normal Browse
    category list. This is a separate, additional way to find new things
    to answer - distinct from Browse's existing "unanswered only" filter
    and from reviewing "Past Answers" history."""
    couple = current_user.couple
    partner = couple.other_member(current_user)
    if partner is None:
        return jsonify({"questions": []})

    pending_activities = (
        couple.activities.join(ActivityContent)
        .join(ActivitySubmission, ActivitySubmission.activity_id == Activity.id)
        .filter(
            ActivityContent.activity_type == "classic_question",
            ActivityContent.active.is_(True),
            ActivitySubmission.user_id == partner.id,
            Activity.revealed_at.is_(None),
        )
        .all()
    )

    unlocked = spicy_unlocked(couple)
    favourite_ids = {f.question_id for f in Favourite.query.filter_by(user_id=current_user.id).all()}

    out = []
    for activity in pending_activities:
        content = activity.content
        if content.category == "spicy" and not unlocked:
            continue
        legacy_id = content.payload.get("legacy_question_id")
        if legacy_id is None:
            continue
        out.append(
            {
                "id": legacy_id,
                "text": content.prompt,
                "category": content.category,
                "is_favourite": legacy_id in favourite_ids,
            }
        )

    return jsonify({"questions": out})


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
