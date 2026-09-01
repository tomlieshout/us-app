import os
from datetime import timedelta


class Config:
    """Base configuration. Values are pulled from environment variables so
    nothing sensitive is ever hardcoded (see README / .env.example)."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")

    # Flask-SQLAlchemy reads DATABASE_URL. Locally this defaults to a SQLite
    # file so the app runs with zero setup. In production, set DATABASE_URL
    # to a Postgres connection string (e.g. from Supabase) and nothing else
    # in the codebase needs to change.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///us.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sessions / cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(days=90)
    REMEMBER_COOKIE_DURATION = timedelta(days=90)

    # WTF / CSRF
    WTF_CSRF_TIME_LIMIT = None  # tokens tied to session lifetime, not a short timer

    # App-specific
    INVITE_CODE_LENGTH = 6
    MIN_ROUNDS_FOR_PREDICTION_PERCENT = 5  # don't show a % until this many prediction rounds are complete


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
