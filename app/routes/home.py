from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.services.home import get_home_data
from app.services.privacy import spicy_unlocked

home_bp = Blueprint("home", __name__)


@home_bp.get("")
@login_required
def get_home():
    data = get_home_data(current_user.couple, current_user, spicy_unlocked(current_user.couple))
    return jsonify(data)
