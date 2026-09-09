from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db

couple_bp = Blueprint("couple", __name__)

VALID_TIMEZONES_HINT = "Use an IANA timezone name, e.g. 'Pacific/Auckland' or 'America/New_York'."


@couple_bp.get("")
@login_required
def get_couple():
    return jsonify(current_user.couple.to_dict())


@couple_bp.patch("")
@login_required
def update_couple():
    """Shared couple settings: display name, timezone, accent colour."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    data = request.get_json(silent=True) or {}
    couple = current_user.couple

    if "name" in data:
        name = (data.get("name") or "").strip()
        couple.name = name or None

    if "timezone" in data:
        tz = (data.get("timezone") or "").strip()
        try:
            ZoneInfo(tz)
        except (ZoneInfoNotFoundError, ValueError):
            return jsonify({"error": "invalid_timezone", "message": VALID_TIMEZONES_HINT}), 400
        couple.timezone = tz

    if "accent_color" in data:
        color = (data.get("accent_color") or "").strip()
        if color:
            couple.accent_color = color

    db.session.commit()
    return jsonify(couple.to_dict())


@couple_bp.post("/delete")
@login_required
def delete_couple():
    """Permanently deletes the couple and everything tied to it (rounds,
    answers, reactions, comments, favourites, memories, both accounts).
    Requires the user to type the confirmation phrase DELETE, per the build
    brief."""
    from app.models import Couple, User

    data = request.get_json(silent=True) or {}
    if (data.get("confirmation") or "").strip() != "DELETE":
        return jsonify({"error": "confirmation_required", "message": "Type DELETE to confirm."}), 400

    couple = current_user.couple
    couple_id = couple.id

    # Answers/reactions/comments cascade via the Round relationship;
    # Favourites and Memories reference users/couples directly so clean
    # those up explicitly.
    from app.models import Favourite, Memory

    user_ids = [u.id for u in couple.ordered_members()]
    Favourite.query.filter(Favourite.user_id.in_(user_ids)).delete(synchronize_session=False)
    Memory.query.filter_by(couple_id=couple_id).delete(synchronize_session=False)

    for round_ in couple.rounds.all():
        db.session.delete(round_)

    for user in couple.ordered_members():
        db.session.delete(user)

    db.session.delete(couple)
    db.session.commit()
    return jsonify({"ok": True, "deleted_couple_id": couple_id})
