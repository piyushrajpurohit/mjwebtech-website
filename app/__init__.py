"""
app/__init__.py — Application Factory — MJ WebTech Pvt. Ltd.
Registers Blueprints, extensions, context processors, and error handlers.
"""

import os
from flask import Flask, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from config import config_map
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db   = SQLAlchemy()
csrf = CSRFProtect()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)


def create_app(env: str = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)

    env = env or os.environ.get("FLASK_ENV", "default")
    app.config.from_object(config_map.get(env, config_map["default"]))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs("instance", exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # ── CORS Configuration ──
    # Read origins from config (set via CORS_ORIGINS environment variable)
    cors_origins_str = app.config.get("CORS_ORIGINS", "")
    if isinstance(cors_origins_str, str):
        cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
    else:
        cors_origins = [cors_origins_str] if cors_origins_str else []
    
    app.logger.info(f"CORS Origins configured: {cors_origins}")
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
            "is_authenticated": bool(user),
            "is_admin": bool(user and user.is_admin),
        }

    # ── Error handlers ──
    from app.routes.errors import register_error_handlers
    register_error_handlers(app)

    # ── Create tables ──
    with app.app_context():
        from app import models  # noqa
        db.create_all()

    return app
