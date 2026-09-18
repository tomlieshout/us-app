from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.services.notifications import list_notifications, mark_all_seen, unseen_count

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("")
@login_required
def get_notifications():
    notifications = list_notifications(current_user)
    return jsonify(
        {
            "notifications": [n.to_dict() for n in notifications],
            "unseen_count": unseen_count(current_user),
        }
    )


@notifications_bp.post("/seen")
@login_required
def mark_seen():
    mark_all_seen(current_user)
    return jsonify({"ok": True})
