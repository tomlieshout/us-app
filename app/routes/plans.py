from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Plan

plans_bp = Blueprint("plans", __name__)

CATEGORY_META = [
    {"key": "movies_shows", "label": "Movies & Shows", "emoji": "🎬"},
    {"key": "dates", "label": "Dates", "emoji": "💕"},
    {"key": "holidays", "label": "Holidays", "emoji": "🎉"},
    {"key": "trips", "label": "Trips", "emoji": "✈️"},
    {"key": "things_to_do", "label": "Things To Do", "emoji": "📝"},
    {"key": "wishlist", "label": "Wishlist", "emoji": "🎁"},
]


def _get_owned_plan(plan_id):
    """Never trust a client-supplied ID without checking couple ownership.
    A cross-couple id and a same-couple-but-nonexistent id are treated
    identically by the caller (both mean "not found") so we never confirm
    or deny that a plan exists for someone outside the couple."""
    plan = Plan.query.get(plan_id)
    if plan is None or plan.couple_id != current_user.couple_id:
        return None
    return plan


def _can_mutate(plan, user):
    """Either partner can edit/delete a shared plan (same rule as Memory).
    A private plan can only be mutated by whoever added it - a partner who
    can't see its content shouldn't be able to change its status/notes/
    title either, since even a status flip is a side-channel leak of
    "something happened to a plan I can't read"."""
    if plan.is_private and plan.added_by_id != user.id:
        return False
    return True


def _matched_plan_ids(couple_id):
    """Shared-interest matching (Task 4.2): exact title + same category,
    tolerant of capitalization/whitespace via Plan.title_key.

    Private plans are excluded entirely - both from the group they'd form
    AND from ever being compared against. If a private plan matched a
    partner's public one, flagging it would tell the partner "your partner
    already has something with this exact title" without them ever seeing
    it - a real leak through the one channel to_dict() otherwise closes off.

    A group only counts as a match once it has plans from >= 2 DISTINCT
    partners - one person adding the same title twice (the "duplicate
    additions" case) must never flag as a match.
    """
    rows = (
        Plan.query.filter_by(couple_id=couple_id, is_private=False)
        .with_entities(Plan.id, Plan.category, Plan.title_key, Plan.added_by_id)
        .all()
    )

    groups = {}
    for plan_id, category, title_key, added_by_id in rows:
        groups.setdefault((category, title_key), []).append((plan_id, added_by_id))

    matched_ids = set()
    for members in groups.values():
        if len({added_by_id for _, added_by_id in members}) >= 2:
            matched_ids.update(plan_id for plan_id, _ in members)
    return matched_ids


def _serialize(plan, matched_ids=None):
    matched_ids = matched_ids if matched_ids is not None else _matched_plan_ids(current_user.couple_id)
    return plan.to_dict(current_user, matched=plan.id in matched_ids)


@plans_bp.get("/categories")
@login_required
def categories():
    counts = dict(
        db.session.query(Plan.category, db.func.count(Plan.id))
        .filter(Plan.couple_id == current_user.couple_id)
        .group_by(Plan.category)
        .all()
    )
    out = [{**c, "count": counts.get(c["key"], 0)} for c in CATEGORY_META]
    return jsonify({"categories": out})


@plans_bp.get("/statuses")
@login_required
def statuses():
    return jsonify({"statuses": [{"key": k, "label": label} for k, label in Plan.STATUSES]})


@plans_bp.get("")
@login_required
def list_plans():
    query = Plan.query.filter_by(couple_id=current_user.couple_id)

    category = request.args.get("category")
    if category:
        if category not in Plan.CATEGORY_KEYS:
            return jsonify({"error": "invalid_category", "message": "Not a real category."}), 400
        query = query.filter_by(category=category)

    status = request.args.get("status")
    if status:
        if status not in Plan.STATUS_KEYS:
            return jsonify({"error": "invalid_status", "message": "Not a real status."}), 400
        query = query.filter_by(status=status)

    plans = query.order_by(Plan.created_at.desc()).all()
    matched_ids = _matched_plan_ids(current_user.couple_id)
    return jsonify({"plans": [_serialize(p, matched_ids) for p in plans]})


@plans_bp.get("/<int:plan_id>")
@login_required
def get_plan(plan_id):
    plan = _get_owned_plan(plan_id)
    if plan is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify(_serialize(plan))


@plans_bp.post("")
@login_required
def create_plan():
    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title_required", "message": "Give it a title."}), 400

    category = data.get("category")
    if category not in Plan.CATEGORY_KEYS:
        return jsonify({"error": "invalid_category", "message": "Pick a real category."}), 400

    status = data.get("status", "someday")
    if status not in Plan.STATUS_KEYS:
        return jsonify({"error": "invalid_status", "message": "Not a real status."}), 400

    plan = Plan(
        couple_id=current_user.couple_id,
        added_by_id=current_user.id,
        title=title,
        category=category,
        status=status,
        notes=(data.get("notes") or "").strip() or None,
        is_private=bool(data.get("is_private", False)),
    )
    db.session.add(plan)
    db.session.commit()
    return jsonify(_serialize(plan)), 201


@plans_bp.patch("/<int:plan_id>")
@login_required
def update_plan(plan_id):
    plan = _get_owned_plan(plan_id)
    if plan is None:
        return jsonify({"error": "not_found"}), 404
    if not _can_mutate(plan, current_user):
        return jsonify({"error": "not_allowed", "message": "Only the person who added this can change it."}), 403

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title_required", "message": "Give it a title."}), 400
        plan.title = title

    if "category" in data:
        category = data.get("category")
        if category not in Plan.CATEGORY_KEYS:
            return jsonify({"error": "invalid_category", "message": "Pick a real category."}), 400
        plan.category = category

    if "status" in data:
        status = data.get("status")
        if status not in Plan.STATUS_KEYS:
            return jsonify({"error": "invalid_status", "message": "Not a real status."}), 400
        plan.status = status

    if "notes" in data:
        plan.notes = (data.get("notes") or "").strip() or None

    if "is_private" in data:
        # Only the creator decides whether their own addition is private,
        # in either direction - a partner flipping someone else's shared
        # item private (or vice versa) isn't something either side asked
        # for, so it's rejected explicitly rather than silently ignored.
        if plan.added_by_id != current_user.id:
            return jsonify({"error": "not_allowed", "message": "Only the person who added this can change its privacy."}), 403
        plan.is_private = bool(data.get("is_private"))

    plan.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize(plan))


@plans_bp.delete("/<int:plan_id>")
@login_required
def delete_plan(plan_id):
    plan = _get_owned_plan(plan_id)
    if plan is None:
        return jsonify({"error": "not_found"}), 404
    if not _can_mutate(plan, current_user):
        return jsonify({"error": "not_allowed", "message": "Only the person who added this can delete it."}), 403

    db.session.delete(plan)
    db.session.commit()
    return jsonify({"ok": True})
