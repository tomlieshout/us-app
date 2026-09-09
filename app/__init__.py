import os

from flask import Flask, jsonify, render_template, request

from app.config import config_by_name
from app.extensions import bcrypt, csrf, db, login_manager, migrate


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Import models so they are registered with SQLAlchemy/Flask-Migrate.
    from app import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return User.query.get(int(user_id))

    _register_blueprints(app)
    _register_error_handlers(app)

    @app.context_processor
    def inject_globals():
        from flask_wtf.csrf import generate_csrf

        return {"csrf_token_value": generate_csrf}

    return app


def _register_blueprints(app):
    from app.routes.activities import activities_bp
    from app.routes.answers import answers_bp
    from app.routes.appreciation import appreciation_bp
    from app.routes.auth import auth_bp
    from app.routes.challenges import challenges_bp
    from app.routes.comments import comments_bp
    from app.routes.couple import couple_bp
    from app.routes.emoji_story import emoji_story_bp
    from app.routes.favourites import favourites_bp
    from app.routes.memories import memories_bp
    from app.routes.pages import pages_bp
    from app.routes.questions import questions_bp
    from app.routes.reactions import reactions_bp
    from app.routes.rounds import rounds_bp
    from app.routes.settings import settings_bp
    from app.routes.spicy import spicy_bp
    from app.routes.stats import stats_bp
    from app.routes.twenty_questions import twenty_questions_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(couple_bp, url_prefix="/api/couple")
    app.register_blueprint(questions_bp, url_prefix="/api/questions")
    app.register_blueprint(rounds_bp, url_prefix="/api/rounds")
    app.register_blueprint(answers_bp, url_prefix="/api/answers")
    app.register_blueprint(reactions_bp, url_prefix="/api/reactions")
    app.register_blueprint(comments_bp, url_prefix="/api/comments")
    app.register_blueprint(favourites_bp, url_prefix="/api/favourites")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(settings_bp, url_prefix="/api/settings")
    app.register_blueprint(spicy_bp, url_prefix="/api/spicy")
    app.register_blueprint(activities_bp, url_prefix="/api/activities")
    app.register_blueprint(emoji_story_bp, url_prefix="/api/emoji-story")
    app.register_blueprint(twenty_questions_bp, url_prefix="/api/twenty-questions")
    app.register_blueprint(challenges_bp, url_prefix="/api/challenges")
    app.register_blueprint(appreciation_bp, url_prefix="/api/appreciation")
    app.register_blueprint(memories_bp, url_prefix="/api/memories")


def _register_error_handlers(app):
    def _wants_json():
        return request.path.startswith("/api/")

    @app.errorhandler(400)
    def bad_request(e):
        if _wants_json():
            return jsonify({"error": "bad_request", "message": str(getattr(e, "description", "Bad request"))}), 400
        return render_template("error.html", code=400, message="Something about that request wasn't right."), 400

    @app.errorhandler(401)
    def unauthorized(e):
        if _wants_json():
            return jsonify({"error": "unauthorized", "message": "Please log in."}), 401
        return render_template("error.html", code=401, message="Please log in."), 401

    @app.errorhandler(403)
    def forbidden(e):
        if _wants_json():
            return jsonify({"error": "forbidden", "message": "You don't have access to that."}), 403
        return render_template("error.html", code=403, message="You don't have access to that."), 403

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json():
            return jsonify({"error": "not_found", "message": "That couldn't be found."}), 404
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled server error")
        if _wants_json():
            return jsonify({"error": "server_error", "message": "Something went wrong on our end."}), 500
        return render_template("error.html", code=500, message="Something went wrong on our end."), 500

    from app.services.privacy import AccessDenied

    @app.errorhandler(AccessDenied)
    def access_denied(e):
        # Deliberately identical to a plain 404: a request for data outside
        # the current user's couple should look indistinguishable from a
        # request for something that doesn't exist at all.
        return not_found(e)

    from app.services.activity_privacy import ActivityAccessDenied

    @app.errorhandler(ActivityAccessDenied)
    def activity_access_denied(e):
        # Same rule, same reasoning, for the new Activity system.
        return not_found(e)

    from app.services.twenty_questions import TwentyQuestionsAccessDenied

    @app.errorhandler(TwentyQuestionsAccessDenied)
    def twenty_questions_access_denied(e):
        return not_found(e)

    from app.services.challenges import ChallengeAccessDenied

    @app.errorhandler(ChallengeAccessDenied)
    def challenge_access_denied(e):
        return not_found(e)

    from app.services.appreciation import AppreciationAccessDenied

    @app.errorhandler(AppreciationAccessDenied)
    def appreciation_access_denied(e):
        return not_found(e)

    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        if _wants_json():
            return jsonify({"error": "csrf", "message": "Your session expired, please refresh and try again."}), 400
        return render_template("error.html", code=400, message="Your session expired. Please refresh."), 400
