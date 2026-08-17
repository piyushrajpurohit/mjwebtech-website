"""
routes/contact.py — Contact form with Flask-WTF, DB storage, email notification.
Includes OTP verification and confirmation emails.
"""

import bleach, re, json, urllib.request, urllib.parse
from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, current_app, jsonify)
from app import csrf, db, limiter
from app.models import Contact, ContactActionLog, OTPVerification
from app.forms  import ContactForm
from app.email_service import send_otp_email, send_confirmation_email

contact_bp = Blueprint("contact", __name__)


def _turnstile_enabled() -> bool:
    return bool(current_app.config.get("TURNSTILE_SECRET_KEY"))


def _verify_turnstile(token: str) -> tuple[bool, str]:
    if not _turnstile_enabled():
        current_app.logger.warning("Turnstile CAPTCHA is not configured, skipping verification.")
        return True, ""

    if not token:
        return False, "CAPTCHA verification is required."

    payload = urllib.parse.urlencode({
        "secret": current_app.config["TURNSTILE_SECRET_KEY"],
        "response": token,
        "remoteip": request.remote_addr,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        if result.get("success"):
            return True, ""

        errors = result.get("error-codes", []) or []
        return False, "CAPTCHA verification failed. " + ", ".join(errors)
    except Exception as exc:
        current_app.logger.error(f"Turnstile verification error: {exc}")
        return False, "CAPTCHA verification failed due to a server error. Please try again."


def _record_contact_action(contact: Contact, action: str, performed_by: str, notes: str | None = None):
    log = ContactActionLog(
        contact_id=contact.id,
        action=action,
        performed_by=performed_by,
        notes=notes,
    )
    db.session.add(log)
    db.session.commit()


def _send_notification(contact: Contact):
    """Send admin email — fails silently if SMTP not configured."""
    try:
        from flask_mail import Message
        from app import mail
        msg = Message(
            subject=f"[MJWebTech] New Contact: {contact.subject}",
            recipients=[current_app.config["CONTACT_EMAIL"]],
            body=(
                f"Name:    {contact.name}\n"
                f"Email:   {contact.email}\n"
                f"Phone:   {contact.phone or 'N/A'}\n"
                f"Subject: {contact.subject}\n\n"
                f"Message:\n{contact.message}"
            ),
        )
        mail.send(msg)
    except Exception as exc:
        current_app.logger.warning(f"Email failed: {exc}")


# ── OTP Routes for Contact Form ──
@contact_bp.route("/contact/send-otp", methods=["POST"])
@csrf.exempt
def send_contact_otp():
    """Send OTP to user before allowing contact form submission."""
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400
    
    try:
        otp_record = OTPVerification.create_otp(email, purpose="contact_verification")
        success = send_otp_email(email, otp_record.otp, purpose="contact form verification")
        
        if success:
            return jsonify({
                "success": True, 
                "message": "OTP sent! Check your email for the verification code.",
                "expires_in": 600
            })

        return jsonify({
            "success": True,
            "message": "OTP generated successfully. For local development, use the code from the server logs if email delivery is unavailable.",
            "expires_in": 600,
            "otp": otp_record.otp,
        })
            
    except Exception as e:
        current_app.logger.error(f"OTP send error: {e}")
        return jsonify({"success": False, "message": "An error occurred. Please try again."}), 500


@contact_bp.route("/contact/verify-otp", methods=["POST"])
@csrf.exempt
def verify_contact_otp():
    """Verify OTP before allowing contact form submission."""
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    otp = (payload.get("otp") or "").strip()
    
    if not email or not otp:
        return jsonify({"success": False, "message": "Email and OTP are required."}), 400
    
    is_valid = OTPVerification.verify_otp(email, otp, purpose="contact_verification")
    
    if is_valid:
        return jsonify({"success": True, "message": "Email verified successfully!"})
    else:
        return jsonify({"success": False, "message": "Invalid or expired OTP. Please request a new one."}), 400


@contact_bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"]) 
def contact():
    form = ContactForm()
    map_embed = current_app.config.get("GOOGLE_MAPS_EMBED", "")
    subject_prefill = request.args.get("subject", "").strip()
    if subject_prefill and subject_prefill in [choice[0] for choice in form.subject.choices]:
        form.subject.data = subject_prefill

    if form.validate_on_submit():
        token = request.form.get("cf-turnstile-response")
        verified, captcha_message = _verify_turnstile(token)
        if not verified:
            flash(captcha_message, "danger")
            return render_template(
                "contact.html",
                form=form,
                map_embed=map_embed,
                turnstile_site_key=current_app.config.get("TURNSTILE_SITE_KEY"),
            )

        entry = Contact(
            name       = bleach.clean(form.name.data,    tags=[], strip=True)[:120],
            email      = bleach.clean(form.email.data,   tags=[], strip=True)[:254],
            company    = bleach.clean(form.company.data or "", tags=[], strip=True)[:200] or None,
            phone      = bleach.clean(form.phone.data or "",  tags=[], strip=True)[:20] or None,
            subject    = bleach.clean(form.subject.data, tags=[], strip=True)[:200],
            message    = bleach.clean(form.message.data, tags=[], strip=True)[:3000],
            ip_address = request.remote_addr,
        )
        db.session.add(entry)
        db.session.commit()
        _record_contact_action(
            entry,
            action="Created",
            performed_by=f"Contact form ({entry.email})",
            notes=f"Inquiry created from public contact form with status {entry.status}.",
        )
        
        # ── Send Admin Notification ──
        _send_notification(entry)
        
        # ── Send User Confirmation Email ──
        try:
            send_confirmation_email(
                email=form.email.data,
                name=form.name.data,
                subject_line="We Received Your Message",
                message=f"Subject: {form.subject.data}\n\nYour message has been received and we will respond within 24 hours.",
                template="contact"
            )
        except Exception as e:
            current_app.logger.warning(f"Confirmation email failed: {e}")
        
        flash("Thank you! Your message has been received. We'll get back to you within 24 hours.", "success")
        return redirect(url_for("contact.contact"))

    return render_template(
        "contact.html",
        form=form,
        map_embed=map_embed,
        turnstile_site_key=current_app.config.get("TURNSTILE_SITE_KEY"),
    )
