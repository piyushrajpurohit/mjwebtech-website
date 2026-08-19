"""
app/__init__.py — Application Factory — MJ WebTech Pvt. Ltd.
Registers Blueprints, extensions, context processors, and error handlers.
"""

import os
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from config import config_map
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from app.security import parse_cors_origins

db   = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def _social_links(app: Flask) -> list[dict]:
    mapping = (
        ("SOCIAL_LINKEDIN", "linkedin", "LinkedIn"),
        ("SOCIAL_TWITTER", "twitter-x", "Twitter/X"),
        ("SOCIAL_FACEBOOK", "facebook", "Facebook"),
        ("SOCIAL_INSTAGRAM", "instagram", "Instagram"),
        ("SOCIAL_YOUTUBE", "youtube", "YouTube"),
    )
    links = []
    for key, icon, label in mapping:
        url = (app.config.get(key) or "").strip()
        if url:
            links.append({"url": url, "icon": icon, "label": label})
    return links


def _widen_otp_column(app: Flask) -> None:
    """Hashed OTPs need more than VARCHAR(6). create_all will not alter Postgres."""
    from sqlalchemy import inspect, text

    try:
        insp = inspect(db.engine)
        if not insp.has_table("otp_verifications"):
            return
        if db.engine.dialect.name != "postgresql":
            return
        db.session.execute(text(
            "ALTER TABLE otp_verifications ALTER COLUMN otp TYPE VARCHAR(255)"
        ))
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        app.logger.warning("Could not widen otp column: %s", exc)


def create_app(env: str = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    env = env or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config_map.get(env, config_map["default"]))

    # Render terminates TLS at the proxy. Without this, Flask sees HTTP and
    # CSRF / secure-cookie checks fail on POST /login.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs("instance", exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    cors_origins = parse_cors_origins(app.config.get("CORS_ORIGINS", ""))
    app.config["CORS_ORIGIN_LIST"] = cors_origins
    app.logger.info("CORS Origins configured: %s", cors_origins)
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # ── Blueprints ──
    from app.routes.main    import main_bp
    from app.routes.contact import contact_bp
    from app.routes.careers import careers_bp
    from app.routes.blog    import blog_bp
    from app.routes.auth    import auth_bp
    from app.routes.api     import api_bp
    from app.routes.admin_contacts import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(careers_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def _enforce_api_origin():
        """Reject cross-origin mutating API calls from unknown sites."""
        if not request.path.startswith("/api/"):
            return
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return
        origin = request.headers.get("Origin")
        if not origin:
            return
        allowed = app.config.get("CORS_ORIGIN_LIST") or []
        if origin.rstrip("/") not in allowed:
            return jsonify({
                "success": False,
                "error": "forbidden_origin",
                "message": "This origin is not allowed to call the API.",
            }), 403

    @app.after_request
    def _security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        if env == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
        return response

    # ── Global template context ──
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        user = None
        if session.get("user_id"):
            from app.models import User
            user = User.query.get(session["user_id"])

        return {
            "company_name":    app.config["COMPANY_NAME"],
            "company_email":   app.config["COMPANY_EMAIL"],
            "company_phone":   app.config["COMPANY_PHONE"],
            "company_address": app.config["COMPANY_ADDRESS"],
            "current_year":    datetime.utcnow().year,
            "is_authenticated": bool(user and user.is_active),
            "is_admin": bool(user and user.is_admin),
            "api_base_url": app.config.get("API_BASE_URL", "").rstrip("/"),
            "social_links": _social_links(app),
        }

    # ── Error handlers ──
    from app.routes.errors import register_error_handlers
    register_error_handlers(app)

    # create_all is a safety net for missing tables (SQLite/dev and first Render
    # boot). Production schema changes should go through Flask-Migrate:
    #   set FLASK_APP=manage
    #   flask db upgrade
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()
        _widen_otp_column(app)

    return app
