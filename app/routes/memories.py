from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Memory

memories_bp = Blueprint("memories", __name__)


def _clean_tags(raw):
    if not raw:
        return []
    if isinstance(raw, str):
        raw = raw.split(",")
    return [t.strip() for t in raw if isinstance(t, str) and t.strip()][:10]


def _parse_date(value):
    """Returns (date_or_none, error_tuple_or_none)."""
    value = (value or "").strip()
    if not value:
        return None, None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date(), None
    except ValueError:
        return None, ("invalid_date", "Use YYYY-MM-DD.")


def _get_owned_memory(memory_id):
    """Never trust a client-supplied ID without checking couple ownership."""
    memory = Memory.query.get(memory_id)
    if memory is None or memory.couple_id != current_user.couple_id:
        return None
    return memory


@memories_bp.get("")
@login_required
def list_memories():
    memories = (
        Memory.query.filter_by(couple_id=current_user.couple_id)
        .order_by(Memory.date.desc().nullslast(), Memory.created_at.desc())
        .all()
    )
    return jsonify({"memories": [m.to_dict() for m in memories]})


@memories_bp.get("/<int:memory_id>")
@login_required
def get_memory(memory_id):
    memory = _get_owned_memory(memory_id)
    if memory is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify(memory.to_dict())


@memories_bp.post("")
@login_required
def create_memory():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title_required", "message": "Give it a title."}), 400

    parsed_date, err = _parse_date(data.get("date"))
    if err:
        return jsonify({"error": err[0], "message": err[1]}), 400

    memory = Memory(
        couple_id=current_user.couple_id,
        created_by_id=current_user.id,
        title=title,
        date=parsed_date,
        description=(data.get("description") or "").strip() or None,
        tags=_clean_tags(data.get("tags")),
    )
    db.session.add(memory)
    db.session.commit()
    return jsonify(memory.to_dict()), 201


@memories_bp.patch("/<int:memory_id>")
@login_required
def update_memory(memory_id):
    memory = _get_owned_memory(memory_id)
    if memory is None:
        return jsonify({"error": "not_found"}), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title_required", "message": "Give it a title."}), 400
        memory.title = title

    if "date" in data:
        parsed_date, err = _parse_date(data.get("date"))
        if err:
            return jsonify({"error": err[0], "message": err[1]}), 400
        memory.date = parsed_date

    if "description" in data:
        memory.description = (data.get("description") or "").strip() or None

    if "tags" in data:
        memory.tags = _clean_tags(data.get("tags"))

    memory.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(memory.to_dict())


@memories_bp.delete("/<int:memory_id>")
@login_required
def delete_memory(memory_id):
    memory = _get_owned_memory(memory_id)
    if memory is None:
        return jsonify({"error": "not_found"}), 404
    db.session.delete(memory)
    db.session.commit()
    return jsonify({"ok": True})
