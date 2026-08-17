"""
config.py — MJ WebTech Pvt. Ltd.
Environment-based configuration for development, testing, and production.
Supports both SQLite (local) and PostgreSQL (remote).
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _database_url():
    """Return a SQLAlchemy-compatible database URL.

    Render may inject postgres://; SQLAlchemy 1.4+ requires postgresql://.
    """
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


class Config:
    """Base configuration — inherited by all environments."""
    
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production-env")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # ── Database Configuration ──
    # LOCAL: SQLite (development only)
    # PRODUCTION: PostgreSQL via DATABASE_URL env var
    SQLALCHEMY_DATABASE_URI = _database_url() or (
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'mjwebtech.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pool settings optimized for production databases
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,      # Recycle connections before timeout
        "pool_pre_ping": True,    # Verify connections before use (critical for remote DB)
        "pool_size": 10,          # Connection pool size for production
        "max_overflow": 5,        # Overflow connections for peak load
        "connect_args": {"connect_timeout": 10},
    }

    # ── File Upload Settings ──
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB limit
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    # ── Email Configuration ──
    MAIL_SERVER   = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS  = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@mjwebtech.in")
    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "info@mjwebtech.in")
    
    # ── CAPTCHA Configuration ──
    TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "")
    TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "")

    # ── Company Information ──
    COMPANY_NAME    = "MJ WebTech Pvt. Ltd."
    COMPANY_EMAIL   = "info@mjwebtech.in"
    COMPANY_PHONE   = "+91-98765-43210"
    COMPANY_ADDRESS = "109, Adarsh Nagar, Near Bajaj Agency, Mahadeva Road, Siwan, Bihar - 841227"
    GOOGLE_MAPS_EMBED = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3597.9!2d84.3627!3d26.2391!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3992fd53f4e3b965:0x21c5230d6e5bfaec!2s109,+Adarsh+Nagar,+Mahadeva+Road,+Siwan,+Bihar+841227!5e0!3m2!1sen!2sin!4v1700000000000!5m2!1sen!2sin"


class DevelopmentConfig(Config):
    """Development configuration — SQLite, debug enabled, localhost CORS."""
    DEBUG = True
    TESTING = False
    # Allow localhost for local frontend development
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000"
    )


class ProductionConfig(Config):
    """Production configuration — PostgreSQL, secure cookies, production CORS."""
    DEBUG = False
    TESTING = False
    
    # ── Security Headers ──
    SESSION_COOKIE_SECURE   = True      # HTTPS only
    SESSION_COOKIE_HTTPONLY = True      # JavaScript cannot access
    SESSION_COOKIE_SAMESITE = "Lax"     # CSRF protection
    REMEMBER_COOKIE_SECURE  = True      # HTTPS only
    
    # ── CORS Configuration ──
    # Production frontend domain(s) — must be set via environment variable
    # Example: https://my-domain.com,https://www.my-domain.com
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "https://my-domain.com"  # Fallback — should be overridden in production
    )
    
    # ── Database ──
    # MUST use PostgreSQL in production (via DATABASE_URL).
    # Accept postgres:// from Render and the canonical postgresql:// form.
    # Only enforce this when actually running in production so config import
    # does not fail during local/dev or static export.
    if os.environ.get("FLASK_ENV") == "production":
        if not (Config.SQLALCHEMY_DATABASE_URI or "").startswith("postgresql://"):
            raise ValueError(
                "PRODUCTION: DATABASE_URL must be a PostgreSQL URL "
                "(postgresql:// or postgres://). SQLite is not supported."
            )


class TestingConfig(Config):
    """Testing configuration — in-memory SQLite, CSRF disabled."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CORS_ORIGINS = "http://localhost:3000"


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig,
}
