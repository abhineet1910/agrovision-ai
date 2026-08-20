import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "instance", "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")
    LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
    LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-1.5-flash")

    try:
        MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", 5))
    except (TypeError, ValueError):
        MAX_UPLOAD_MB = 5
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(basedir, "app", "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
