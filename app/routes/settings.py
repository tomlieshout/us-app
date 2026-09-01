from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, logout_user

from app.extensions import db
from app.models import Answer, Comment, Favourite, Reaction

settings_bp = Blueprint("settings", __name__)

VALID_DARK_MODE = {"system", "light", "dark"}


@settings_bp.patch("/profile")
@login_required
def update_profile():
    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "validation", "message": "Name can't be empty."}), 400
        current_user.name = name
    if "avatar_color" in data and data.get("avatar_color"):
        current_user.avatar_color = data["avatar_color"]
    if "dark_mode_pref" in data:
        pref = data.get("dark_mode_pref")
        if pref not in VALID_DARK_MODE:
            return jsonify({"error": "validation", "message": "Invalid theme preference."}), 400
        current_user.dark_mode_pref = pref

    db.session.commit()
    return jsonify(current_user.to_private_dict())


@settings_bp.post("/password")
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not current_user.check_password(current_password):
        return jsonify({"error": "invalid_credentials", "message": "Current password is incorrect."}), 401
    if len(new_password) < 8:
        return jsonify({"error": "validation", "message": "New password must be at least 8 characters."}), 400

    current_user.set_password(new_password)
    db.session.commit()
    return jsonify({"ok": True})


@settings_bp.post("/spicy")
@login_required
def set_spicy_opt_in():
    """Each partner independently opts in/out. The category only actually
    unlocks (see services.privacy.spicy_unlocked) once BOTH partners have
    enabled=true here."""
    data = request.get_json(silent=True) or {}
    enabled = bool(data.get("enabled"))

    if enabled:
        if not data.get("adult_confirmation"):
            return jsonify(
                {
                    "error": "confirmation_required",
                    "message": "Please confirm you're both comfortable exploring this together and are an adult.",
                }
            ), 400
        current_user.is_adult_confirmed = True
        current_user.spicy_opt_in = True
    else:
        current_user.spicy_opt_in = False

    db.session.commit()
    return jsonify({"user": current_user.to_private_dict(), "couple": current_user.couple.to_dict()})


@settings_bp.post("/delete-answers")
@login_required
def delete_my_answers():
    """Erases the content of every answer this user has ever submitted.
    Rounds already revealed to the partner stay revealed (the partner
    already saw them), but the stored content is gone from the database."""
    Answer.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"ok": True})


@settings_bp.post("/delete-account")
@login_required
def delete_account():
    """Deletes this user's login and personal content. If they were the
    last member of the couple, the (now-empty) couple is removed too. The
    other partner's own answers/comments/reactions are untouched."""
    user = current_user
    couple = user.couple
    logout_user()

    Reaction.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Comment.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Favourite.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Answer.query.filter_by(user_id=user.id).delete(synchronize_session=False)

    remaining_partner = couple.other_member(user)
    db.session.delete(user)
    db.session.flush()

    if remaining_partner is None:
        for round_ in couple.rounds.all():
            db.session.delete(round_)
        db.session.delete(couple)

    db.session.commit()
    return jsonify({"ok": True})
