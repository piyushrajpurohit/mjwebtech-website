"""
routes/api.py — JSON REST API endpoints for frontend integration.
Provides secure, validated endpoints for items, authentication, and contact submissions.
"""

import re
import bleach
from flask import Blueprint, jsonify, request, current_app, session
from app import csrf, db, limiter
from app.models import ApiItem, Contact, ContactActionLog, User
from app.email_service import send_confirmation_email
from app.auth_utils import login_required
from app.routes.auth import send_register_otp, verify_register_otp, resend_register_otp
from app.routes.contact import send_contact_otp as contact_send_otp, verify_contact_otp as contact_verify_otp, _verify_turnstile
from app.routes.careers import send_application_otp as career_send_otp, verify_application_otp as career_verify_otp

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _json_error(message: str, status_code: int = 400, error_code: str = "bad_request"):
    return jsonify({
        "success": False,
        "error": error_code,
        "message": message,
    }), status_code


def _is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


@api_bp.route("/health", methods=["GET"])
@csrf.exempt
def health():
    return jsonify({
        "success": True,
        "message": "API is healthy",
        "service": "mjwebtech",
    })


@api_bp.route("/items", methods=["GET"])
@csrf.exempt
def list_items():
    items = ApiItem.query.order_by(ApiItem.created_at.desc()).all()
    return jsonify({
        "success": True,
        "items": [item.to_dict() for item in items],
    })


@api_bp.route("/items", methods=["POST"])
@login_required
@csrf.exempt
def create_item():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _json_error("JSON object payload is required.", 400, "invalid_payload")

    name = (payload.get("name") or "").strip()
    description = (payload.get("description") or "").strip()

    if not name or len(name) < 2:
        return _json_error("Name is required and must be at least 2 characters long.", 400, "invalid_name")

    if not description or len(description) < 5:
        return _json_error("Description is required and must be at least 5 characters long.", 400, "invalid_description")

    item = ApiItem(
        name=bleach.clean(name, tags=[], strip=True)[:120],
        description=bleach.clean(description, tags=[], strip=True)[:2000],
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Item created successfully.",
        "item": item.to_dict(),
    }), 201


@api_bp.route("/login", methods=["POST"])
@csrf.exempt
def login():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _json_error("JSON object payload is required.", 400, "invalid_payload")

    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email:
        return _json_error("Email is required.", 400, "missing_email")

    if not password:
        return _json_error("Password is required.", 400, "missing_password")

    if not _is_valid_email(email):
        return _json_error("Please provide a valid email address.", 400, "invalid_email")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return _json_error("Invalid email or password.", 401, "unauthorized")

    session["user_id"] = user.id
    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": user.to_dict(),
    })


@api_bp.route("/auth/login", methods=["POST"])
@csrf.exempt
def login_alias():
    return login()


@api_bp.route("/register", methods=["POST"])
@csrf.exempt
def register():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _json_error("JSON object payload is required.", 400, "invalid_payload")

    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not name or len(name) < 2:
        return _json_error("Name is required and must be at least 2 characters long.", 400, "invalid_name")

    if not email or not _is_valid_email(email):
        return _json_error("Please provide a valid email address.", 400, "invalid_email")

    if not password or len(password) < 6:
        return _json_error("Password must be at least 6 characters long.", 400, "weak_password")

    if User.query.filter_by(email=email).first():
        return _json_error("An account with this email already exists.", 409, "email_taken")

    user = User(name=bleach.clean(name, tags=[], strip=True)[:120], email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    return jsonify({
        "success": True,
        "message": "Registration successful.",
        "user": user.to_dict(),
    }), 201


@api_bp.route("/profile", methods=["GET"])
@login_required
@csrf.exempt
def profile():
    user = User.query.get(session.get("user_id"))
    if not user:
        return _json_error("Authenticated user not found.", 401, "unauthorized")

    return jsonify({
        "success": True,
        "user": user.to_dict(),
    })


@api_bp.route("/logout", methods=["POST"])
@login_required
@csrf.exempt
def api_logout():
    session.pop("user_id", None)
    return jsonify({
        "success": True,
        "message": "Logged out successfully.",
    })


@api_bp.route("/auth/send-otp", methods=["POST"])
@csrf.exempt
def api_send_register_otp():
    return send_register_otp()


@api_bp.route("/auth/verify-otp", methods=["POST"])
@csrf.exempt
def api_verify_register_otp():
    return verify_register_otp()


@api_bp.route("/auth/resend-otp", methods=["POST"])
@csrf.exempt
def api_resend_register_otp():
    return resend_register_otp()


@api_bp.route("/careers/send-otp", methods=["POST"])
@csrf.exempt
def api_send_career_otp():
    return career_send_otp()


@api_bp.route("/careers/verify-otp", methods=["POST"])
@csrf.exempt
def api_verify_career_otp():
    return career_verify_otp()


@api_bp.route("/contact/send-otp", methods=["POST"])
@csrf.exempt
def api_send_contact_otp():
    return contact_send_otp()


@api_bp.route("/contact/verify-otp", methods=["POST"])
@csrf.exempt
def api_verify_contact_otp():
    return contact_verify_otp()


@api_bp.route("/contact", methods=["POST"])
@csrf.exempt
@limiter.limit("10 per hour")
def submit_contact():
    payload = request.get_json(silent=True) or {}
    turnstile_token = payload.get("turnstile_token") or payload.get("cf-turnstile-response")

    if current_app.config.get("TURNSTILE_SECRET_KEY"):
        if not turnstile_token:
            return _json_error("CAPTCHA verification is required.", 400, "captcha_required")

        verified, captcha_message = _verify_turnstile(turnstile_token)
        if not verified:
            return _json_error(captcha_message or "CAPTCHA verification failed.", 400, "captcha_failed")
    if not isinstance(payload, dict):
        return _json_error("JSON object payload is required.", 400, "invalid_payload")

    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    company = (payload.get("company") or "").strip()
    phone = (payload.get("phone") or "").strip()
    subject = (payload.get("subject") or "").strip()
    message = (payload.get("message") or "").strip()

    if not name or len(name) < 2:
        return _json_error("Name is required.", 400, "invalid_name")

    if not email or not _is_valid_email(email):
        return _json_error("A valid email address is required.", 400, "invalid_email")

    if not subject or len(subject) < 3:
        return _json_error("Subject is required.", 400, "invalid_subject")

    if not message or len(message) < 10:
        return _json_error("Message must be at least 10 characters long.", 400, "invalid_message")

    entry = Contact(
        name=bleach.clean(name, tags=[], strip=True)[:120],
        email=email,
        company=bleach.clean(company, tags=[], strip=True)[:200] or None,
        phone=bleach.clean(phone, tags=[], strip=True)[:20] or None,
        subject=bleach.clean(subject, tags=[], strip=True)[:200],
        message=bleach.clean(message, tags=[], strip=True)[:3000],
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    db.session.commit()

    log = ContactActionLog(
        contact_id=entry.id,
        action="Created",
        performed_by=f"API contact submit ({email})",
        notes=f"Contact created via API submission.",
    )
    db.session.add(log)
    db.session.commit()

    try:
        send_confirmation_email(
            email=email,
            name=name,
            subject_line="We Received Your Message",
            message=f"Subject: {subject}\n\nYour message has been received and we will respond within 24 hours.",
            template="contact",
        )
    except Exception as exc:  # pragma: no cover - best effort email
        current_app.logger.warning("Contact confirmation email failed: %s", exc)

    return jsonify({
        "success": True,
        "message": "Your message has been received. We will get back to you shortly.",
    }), 201
