from flask import Blueprint, current_app, jsonify
from flask_login import current_user, login_required

from app.services.stats import compute_competitive_stats, compute_together_stats

stats_bp = Blueprint("stats", __name__)


@stats_bp.get("")
@login_required
def get_stats():
    min_for_percent = current_app.config.get("MIN_ROUNDS_FOR_PREDICTION_PERCENT", 5)
    couple = current_user.couple
    return jsonify(
        {
            "competitive": compute_competitive_stats(couple, min_for_percent=min_for_percent),
            "together": compute_together_stats(current_user),
        }
    )
