import re

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import Couple, User

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")


def _validate_credentials(name, username, password):
    errors = []
    if not name or not name.strip():
        errors.append("Please enter your name.")
    if not username or not USERNAME_RE.match(username):
        errors.append("Username must be 3-30 characters (letters, numbers, . _ -).")
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    return errors


@auth_bp.post("/register-couple")
def register_couple():
    """Step 1 of onboarding: create a brand-new couple and its first member."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    username = (data.get("username") or "").strip().lower()
    email = (data.get("email") or "").strip().lower() or None
    password = data.get("password") or ""

    errors = _validate_credentials(name, username, password)
    if errors:
        return jsonify({"error": "validation", "message": errors[0], "errors": errors}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username_taken", "message": "That username is already taken."}), 400
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "email_taken", "message": "That email is already registered."}), 400

    couple = Couple(invite_code=Couple.make_unique_invite_code())
    db.session.add(couple)
    db.session.flush()  # get couple.id

    user = User(couple_id=couple.id, name=name, username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user, remember=True)
    return jsonify({"couple": couple.to_dict(), "user": user.to_private_dict()}), 201


@auth_bp.post("/join-couple")
def join_couple():
    """Step 1b of onboarding: the second partner joins with an invite code."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    username = (data.get("username") or "").strip().lower()
    email = (data.get("email") or "").strip().lower() or None
    password = data.get("password") or ""
    invite_code = (data.get("invite_code") or "").strip().upper()

    errors = _validate_credentials(name, username, password)
    if not invite_code:
        errors.append("Please enter your partner's invite code.")
    if errors:
        return jsonify({"error": "validation", "message": errors[0], "errors": errors}), 400

    couple = Couple.query.filter_by(invite_code=invite_code).first()
    if not couple:
        return jsonify({"error": "invalid_code", "message": "That invite code doesn't look right."}), 404
    if couple.member_count >= 2:
        return jsonify({"error": "couple_full", "message": "This couple already has two members."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username_taken", "message": "That username is already taken."}), 400
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "email_taken", "message": "That email is already registered."}), 400

    user = User(couple_id=couple.id, name=name, username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    login_user(user, remember=True)
    return jsonify({"couple": couple.to_dict(), "user": user.to_private_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid_credentials", "message": "Incorrect username or password."}), 401

    login_user(user, remember=True)
    return jsonify({"couple": user.couple.to_dict(), "user": user.to_private_dict()})


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False})
    return jsonify(
        {
            "authenticated": True,
            "user": current_user.to_private_dict(),
            "couple": current_user.couple.to_dict(),
        }
    )
