"""
routes/auth.py — User registration with OTP verification.
Provides registration flow with email verification before account creation.
"""

import re
from urllib.parse import urlparse
from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, current_app, jsonify, session)
from app import db, limiter
from app.models import OTPVerification, User
from app.email_service import otp_send_response, send_otp_email, send_confirmation_email
from app.security import MIN_PASSWORD_LENGTH, email_otp_verified, json_payload, mark_email_verified

auth_bp = Blueprint("auth", __name__)


def is_safe_url(target):
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and parsed.path.startswith("/")


def _establish_session(user: User) -> None:
    session.clear()
    session["user_id"] = user.id


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    """Render the login page and handle credentials."""
    next_page = request.args.get("next") if request.method == "GET" else request.form.get("next")

    if session.get("user_id"):
        if is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html", next_page=next_page)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password) or not user.is_active:
            flash("Invalid email or password.", "danger")
            return render_template("login.html", next_page=next_page)

        _establish_session(user)
        flash("Login successful.", "success")
        if is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for("main.dashboard"))

    return render_template("login.html", next_page=next_page)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def register():
    """User registration page."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not name or len(name) < 2:
            flash("Please enter your full name.", "danger")
            return render_template("register.html")
        
        if not email:
            flash("Email is required.", "danger")
            return render_template("register.html")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash("Please enter a valid email address.", "danger")
            return render_template("register.html")
        
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            flash(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", "danger")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")
        
        if not email_otp_verified(email, "registration"):
            flash("Please verify your email first.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("register.html")

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session.pop("otp_verified:registration", None)
        session.pop("otp_verified_email", None)
        _establish_session(user)

        send_confirmation_email(
            email=email,
            name=name,
            subject_line="Welcome to MJ WebTech",
            message="Your account has been created successfully.",
            template="general"
        )

        flash(f"Registration successful! Welcome, {name}.", "success")
        return redirect(url_for("main.index"))
    
    return render_template("register.html")


@auth_bp.route("/auth/send-otp", methods=["POST"])
@limiter.limit("5 per hour")
def send_register_otp():
    """Send OTP for registration email verification."""
    payload = json_payload()
    email = (payload.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400
    
    try:
        otp_record = OTPVerification.create_otp(email, purpose="registration")
        success = send_otp_email(email, otp_record.plain_otp, purpose="account registration")
        return otp_send_response(success, otp_record.plain_otp)
            
    except Exception as e:
        current_app.logger.error(f"OTP send error: {e}")
        return jsonify({"success": False, "message": "An error occurred. Please try again."}), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """End the authenticated session and redirect to the homepage."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/auth/verify-otp", methods=["POST"])
@limiter.limit("10 per minute")
def verify_register_otp():
    """Verify OTP for registration and issue a signed token."""
    payload = json_payload()
    email = (payload.get("email") or "").strip().lower()
    otp = (payload.get("otp") or "").strip()
    
    if not email or not otp:
        return jsonify({"success": False, "message": "Email and OTP are required."}), 400
    
    is_valid = OTPVerification.verify_otp(email, otp, purpose="registration")
    
    if is_valid:
        token = mark_email_verified(email, "registration")
        session["otp_verified_email"] = email
        return jsonify({
            "success": True,
            "message": "Email verified! You can now complete your registration.",
            "verification_token": token,
        })
    return jsonify({"success": False, "message": "Invalid or expired OTP. Please request a new one."}), 400


@auth_bp.route("/auth/resend-otp", methods=["POST"])
@limiter.limit("5 per hour")
def resend_register_otp():
    """Resend OTP for registration."""
    payload = json_payload()
    email = (payload.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400
    
    try:
        otp_record = OTPVerification.create_otp(email, purpose="registration")
        success = send_otp_email(email, otp_record.plain_otp, purpose="account registration")
        return otp_send_response(success, otp_record.plain_otp, resent=True)
            
    except Exception as e:
        current_app.logger.error(f"OTP resend error: {e}")
        return jsonify({"success": False, "message": "An error occurred. Please try again."}), 500
