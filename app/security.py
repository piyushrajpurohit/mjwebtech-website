"""Security helpers: OTP tokens, upload checks, CORS origin parsing."""

from __future__ import annotations

import os
import uuid
from typing import Optional

from flask import current_app, request, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.utils import secure_filename

OTP_TOKEN_MAX_AGE = 600
MIN_PASSWORD_LENGTH = 8

PDF_MAGIC = b"%PDF"
DOC_MAGIC = b"\xd0\xcf\x11\xe0"
ZIP_MAGIC = b"PK"


def parse_cors_origins(value: str | None) -> list[str]:
    if not value:
        return []
    return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]


def json_payload() -> dict:
    payload = request.get_json(silent=True) or {}
    return payload if isinstance(payload, dict) else {}


def _otp_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="mj-otp-v1")


def issue_otp_token(email: str, purpose: str) -> str:
    return _otp_serializer().dumps({
        "email": (email or "").strip().lower(),
        "purpose": purpose,
    })


def otp_token_valid(
    token: str | None,
    email: str,
    purpose: str,
    max_age: int = OTP_TOKEN_MAX_AGE,
) -> bool:
    if not token:
        return False
    try:
        data = _otp_serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return False
    return (
        data.get("email") == (email or "").strip().lower()
        and data.get("purpose") == purpose
    )


def mark_email_verified(email: str, purpose: str) -> str:
    """Record OTP success in the session and return a signed token for cross-origin APIs."""
    email = (email or "").strip().lower()
    session[f"otp_verified:{purpose}"] = email
    return issue_otp_token(email, purpose)


def _token_from_request() -> str:
    token = request.form.get("verification_token") or ""
    if token:
        return token
    payload = json_payload()
    return (payload.get("verification_token") or "").strip()


def email_otp_verified(email: str, purpose: str, token: str | None = None) -> bool:
    email = (email or "").strip().lower()
    if session.get(f"otp_verified:{purpose}") == email:
        return True
    if token is None:
        token = _token_from_request()
    return otp_token_valid(token, email, purpose)


def save_resume(file_storage) -> tuple[Optional[str], Optional[str]]:
    """Save a resume outside static/. Returns (stored_name, error_message)."""
    allowed_ext = current_app.config["ALLOWED_EXTENSIONS"]
    allowed_mime = current_app.config["ALLOWED_MIME_TYPES"]
    max_size = current_app.config["MAX_CONTENT_LENGTH"]
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    filename = secure_filename(file_storage.filename or "")
    if not filename or "." not in filename:
        return None, "Please upload a valid resume file."

    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_ext:
        return None, "Only PDF, DOC, or DOCX files are allowed."

    mime = (file_storage.mimetype or "").lower()
    if mime and mime not in allowed_mime and mime != "application/octet-stream":
        return None, "Resume file type is not allowed."

    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > max_size:
        return None, "Resume file must be under 5 MB."

    header = file_storage.read(8)
    file_storage.seek(0)
    if ext == "pdf" and not header.startswith(PDF_MAGIC):
        return None, "The uploaded file is not a valid PDF."
    if ext == "doc" and not header.startswith(DOC_MAGIC):
        return None, "The uploaded file is not a valid Word document."
    if ext == "docx" and not header.startswith(ZIP_MAGIC):
        return None, "The uploaded file is not a valid Word document."

    stored = f"{uuid.uuid4().hex}_{filename}"
    file_storage.save(os.path.join(upload_folder, stored))
    return stored, None


def is_safe_upload_name(name: str | None) -> bool:
    if not name:
        return False
    if "/" in name or "\\" in name or ".." in name:
        return False
    return name == os.path.basename(name)
