"""
20 Questions business logic and serialization. Kept entirely separate
from the Activity system on purpose (see app/models/twenty_questions.py).

Turn order is enforced here, server-side, in exactly two checks that
matter:
    - ask_question(): rejects if the previous turn exists and is still
      unanswered (guesser can't pile up questions), and rejects if it's
      not actually this user's turn to ask (only the guesser can ask).
    - answer_question(): rejects if there's no pending (unanswered) turn,
      and rejects if it's not this user's turn to answer (only the
      chooser can answer).
A client that tries to skip ahead - ask twice in a row, answer someone
else's question, answer before a question exists - gets a 400 with a
plain-English reason, never a silently-accepted out-of-order write.
"""

from datetime import datetime

from app.extensions import db
from app.models import TwentyQuestionsGame, TwentyQuestionsTurn
from app.models.twenty_questions import MAX_TURNS, SECRET_CATEGORIES


class TwentyQuestionsError(Exception):
    """A well-formed but invalid request - wrong turn, wrong role, game
    already over, bad input. Routes map this to 400."""


class TwentyQuestionsAccessDenied(Exception):
    """Game doesn't belong to the current user's couple. Routes map this
    to a plain 404, same convention as every other *AccessDenied here."""


def get_owned_game(game_id, user):
    game = TwentyQuestionsGame.query.get(game_id)
    if game is None or game.couple_id != user.couple_id:
        raise TwentyQuestionsAccessDenied()
    return game


def get_current_game(couple):
    """The couple's in-progress game if there is one, otherwise their
    most recently finished one (so a completed game's result stays
    viewable), otherwise None if they've never played."""
    in_progress = (
        TwentyQuestionsGame.query.filter_by(couple_id=couple.id, status="in_progress")
        .order_by(TwentyQuestionsGame.created_at.desc())
        .first()
    )
    if in_progress:
        return in_progress
    return (
        TwentyQuestionsGame.query.filter_by(couple_id=couple.id)
        .order_by(TwentyQuestionsGame.created_at.desc())
        .first()
    )


def create_game(couple, chooser, category, secret_text):
    if category not in SECRET_CATEGORIES:
        raise TwentyQuestionsError("Choose a category: person, place, or thing.")
    secret_text = (secret_text or "").strip()
    if not secret_text:
        raise TwentyQuestionsError("Write down your secret.")
    if len(secret_text) > 200:
        raise TwentyQuestionsError("Keep the secret under 200 characters.")

    guesser = couple.other_member(chooser)
    if guesser is None:
        raise TwentyQuestionsError("Your partner needs to join before you can play.")

    existing = TwentyQuestionsGame.query.filter_by(couple_id=couple.id, status="in_progress").first()
    if existing is not None:
        raise TwentyQuestionsError("Finish or abandon your current game before starting a new one.")

    game = TwentyQuestionsGame(
        couple_id=couple.id,
        chooser_user_id=chooser.id,
        guesser_user_id=guesser.id,
        secret_category=category,
        secret_text=secret_text,
        status="in_progress",
    )
    db.session.add(game)
    db.session.commit()
    return game


def ask_question(game, user, question_text, is_guess=False):
    if game.status != "in_progress":
        raise TwentyQuestionsError("This game has already finished.")
    if user.id != game.guesser_user_id:
        raise TwentyQuestionsError("Only the guesser can ask questions.")

    turns = game.turns.order_by(TwentyQuestionsTurn.turn_number.asc()).all()
    if turns and turns[-1].answer is None:
        raise TwentyQuestionsError("Wait for your last question to be answered first.")
    if len(turns) >= MAX_TURNS:
        raise TwentyQuestionsError(f"You've already used all {MAX_TURNS} questions.")

    question_text = (question_text or "").strip()
    if not question_text:
        raise TwentyQuestionsError("Write a question first.")
    if len(question_text) > 300:
        raise TwentyQuestionsError("Keep your question under 300 characters.")

    turn = TwentyQuestionsTurn(
        game_id=game.id,
        turn_number=len(turns) + 1,
        question_text=question_text,
        is_guess=bool(is_guess),
    )
    db.session.add(turn)
    db.session.commit()
    return turn


def answer_question(game, user, answer_value):
    if game.status != "in_progress":
        raise TwentyQuestionsError("This game has already finished.")
    if user.id != game.chooser_user_id:
        raise TwentyQuestionsError("Only the chooser can answer.")

    pending = game.turns.order_by(TwentyQuestionsTurn.turn_number.desc()).first()
    if pending is None or pending.answer is not None:
        raise TwentyQuestionsError("There's no question waiting to be answered.")

    if pending.is_guess:
        if answer_value not in ("correct", "incorrect"):
            raise TwentyQuestionsError("Mark the guess as correct or incorrect.")
    else:
        if answer_value not in ("yes", "no"):
            raise TwentyQuestionsError("Answer yes or no.")

    pending.answer = answer_value
    pending.answered_at = datetime.utcnow()

    if pending.is_guess and answer_value == "correct":
        game.status = "won"
        game.completed_at = datetime.utcnow()
    elif pending.turn_number >= MAX_TURNS:
        game.status = "lost"
        game.completed_at = datetime.utcnow()

    db.session.commit()
    return pending


def abandon_game(game, user):
    if user.id not in (game.chooser_user_id, game.guesser_user_id):
        raise TwentyQuestionsAccessDenied()
    if game.status != "in_progress":
        raise TwentyQuestionsError("This game has already finished.")
    game.status = "abandoned"
    game.completed_at = datetime.utcnow()
    db.session.commit()
    return game


def serialize_turn(turn):
    return {
        "turn_number": turn.turn_number,
        "question_text": turn.question_text,
        "is_guess": turn.is_guess,
        "answer": turn.answer,
        "asked_at": turn.asked_at.isoformat() + "Z",
        "answered_at": turn.answered_at.isoformat() + "Z" if turn.answered_at else None,
    }


def serialize_game(game, viewer):
    is_chooser = viewer.id == game.chooser_user_id
    is_guesser = viewer.id == game.guesser_user_id
    turns = game.turns.order_by(TwentyQuestionsTurn.turn_number.asc()).all()

    if game.status != "in_progress":
        next_action = None
    elif not turns or turns[-1].answer is not None:
        next_action = "ask"
    else:
        next_action = "answer"

    payload = {
        "game_id": game.id,
        "status": game.status,  # in_progress | won | lost | abandoned
        "category": game.secret_category,  # a helpful hint shown from the start, not the secret itself
        "chooser_user_id": game.chooser_user_id,
        "guesser_user_id": game.guesser_user_id,
        "is_chooser": is_chooser,
        "is_guesser": is_guesser,
        "turn_count": len(turns),
        "max_turns": MAX_TURNS,
        "turns": [serialize_turn(t) for t in turns],
        "next_action": next_action,  # "ask" | "answer" | None (game over)
        "created_at": game.created_at.isoformat() + "Z",
        "completed_at": game.completed_at.isoformat() + "Z" if game.completed_at else None,
    }

    # The secret itself - never sent to the guesser while the game is
    # still in progress. Absent from the response entirely, not null.
    if is_chooser or game.status != "in_progress":
        payload["secret_text"] = game.secret_text

    return payload
