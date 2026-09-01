from flask import Blueprint, current_app, jsonify
from flask_login import current_user, login_required

from app.services.stats import compute_couple_stats

stats_bp = Blueprint("stats", __name__)


@stats_bp.get("")
@login_required
def get_stats():
    min_rounds = current_app.config.get("MIN_ROUNDS_FOR_PREDICTION_PERCENT", 5)
    return jsonify(compute_couple_stats(current_user, min_rounds_for_percent=min_rounds))
