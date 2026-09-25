import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-this-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'uairotas.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = False
    MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN", "").strip()
    TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")
    SESSION_COOKIE_SECURE = APP_ENV == "production"
    REMEMBER_COOKIE_SECURE = APP_ENV == "production"
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 512 * 1024
    MAX_FORM_PARTS = 100
    LOGIN_ATTEMPT_LIMIT = 5
    LOGIN_IP_LIMIT = 30
    LOGIN_WINDOW_SECONDS = 900
    TRUSTED_HOSTS = [h.strip() for h in os.getenv("TRUSTED_HOSTS", "").split(",") if h.strip()] or None
