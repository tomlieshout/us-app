"""
Appreciation business logic. See app/models/appreciation.py for why this
is entirely separate from the Activity system - there's no privacy
dimension to gate here at all.

Explicit design decisions worth being upfront about (the brief frames
View/React/Keep/Delete as things "the recipient" can do, grammatically):
  - View, React, and Keep are recipient-only actions - it's their
    appreciation to engage with.
  - Delete is allowed for EITHER the sender or the recipient, not just
    the recipient the brief's wording literally names. A sender being
    able to retract something they regret sending (a typo, sent in the
    wrong mood, etc.) felt like the more complete, real-world-sensible
    reading of "delete where appropriate" - flagged here rather than
    silently assumed, since it's the one place this implementation goes
    beyond the literal text.
  - Nothing about seen/reaction/kept status is hidden between sender and
    recipient - there is no privacy dimension to this feature at all, so
    both sides can always see the full state once a message exists.
"""

from datetime import datetime

from app.extensions import db
from app.models import Appreciation
from app.models.appreciation import MAX_MESSAGE_LENGTH
from app.models.reaction import REACTION_TYPES


class AppreciationError(Exception):
    """A well-formed but invalid request. Routes map this to 400."""


class AppreciationAccessDenied(Exception):
    """Appreciation doesn't belong to the current user's couple. Routes
    map this to a plain 404, same convention as every other
    *AccessDenied here."""


def get_owned_appreciation(appreciation_id, user):
    appreciation = Appreciation.query.get(appreciation_id)
    if appreciation is None or appreciation.couple_id != user.couple_id:
        raise AppreciationAccessDenied()
    return appreciation


def send_appreciation(couple, sender, message_text):
    message_text = (message_text or "").strip()
    if not message_text:
        raise AppreciationError("Write something before sending.")
    if len(message_text) > MAX_MESSAGE_LENGTH:
        raise AppreciationError(f"Keep it under {MAX_MESSAGE_LENGTH} characters.")

    recipient = couple.other_member(sender)
    if recipient is None:
        raise AppreciationError("Your partner needs to join before you can send one.")

    appreciation = Appreciation(
        couple_id=couple.id,
        sender_user_id=sender.id,
        recipient_user_id=recipient.id,
        message_text=message_text,
    )
    db.session.add(appreciation)
    db.session.commit()
    return appreciation


def mark_seen(appreciation, user):
    if user.id != appreciation.recipient_user_id:
        raise AppreciationError("Only the recipient can do that.")
    if not appreciation.is_seen:
        appreciation.is_seen = True
        appreciation.seen_at = datetime.utcnow()
        db.session.commit()
    return appreciation


def react(appreciation, user, reaction_type):
    if user.id != appreciation.recipient_user_id:
        raise AppreciationError("Only the recipient can react.")
    if reaction_type not in REACTION_TYPES:
        raise AppreciationError("Unknown reaction type.")
    appreciation.reaction_type = reaction_type
    db.session.commit()
    return appreciation


def remove_reaction(appreciation, user):
    if user.id != appreciation.recipient_user_id:
        raise AppreciationError("Only the recipient can do that.")
    appreciation.reaction_type = None
    db.session.commit()
    return appreciation


def toggle_keep(appreciation, user):
    if user.id != appreciation.recipient_user_id:
        raise AppreciationError("Only the recipient can keep it.")
    appreciation.is_kept = not appreciation.is_kept
    db.session.commit()
    return appreciation


def delete_appreciation(appreciation, user):
    if user.id not in (appreciation.sender_user_id, appreciation.recipient_user_id):
        raise AppreciationAccessDenied()
    db.session.delete(appreciation)
    db.session.commit()


def list_received(user, unseen_only=False):
    query = Appreciation.query.filter_by(recipient_user_id=user.id)
    if unseen_only:
        query = query.filter_by(is_seen=False)
    return query.order_by(Appreciation.created_at.desc()).all()


def list_sent(user):
    return (
        Appreciation.query.filter_by(sender_user_id=user.id)
        .order_by(Appreciation.created_at.desc())
        .all()
    )


def unseen_count(user):
    return Appreciation.query.filter_by(recipient_user_id=user.id, is_seen=False).count()


def serialize_appreciation(appreciation, viewer):
    return {
        "id": appreciation.id,
        "message_text": appreciation.message_text,
        "sender_user_id": appreciation.sender_user_id,
        "sender_name": appreciation.sender.name,
        "recipient_user_id": appreciation.recipient_user_id,
        "recipient_name": appreciation.recipient.name,
        "is_from_me": viewer.id == appreciation.sender_user_id,
        "is_seen": appreciation.is_seen,
        "seen_at": appreciation.seen_at.isoformat() + "Z" if appreciation.seen_at else None,
        "is_kept": appreciation.is_kept,
        "reaction_type": appreciation.reaction_type,
        "created_at": appreciation.created_at.isoformat() + "Z",
    }
