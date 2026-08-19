"""
routes/careers.py — Job listings and application form with secure file upload.
Uses Flask-WTF CareerForm for full validation + CSRF.
Includes OTP verification and confirmation emails.
"""

import bleach
from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, current_app, jsonify, session)
from app import csrf, db, limiter
from app.auth_utils import login_required
from app.models import JobApplication, OTPVerification
from app.forms  import CareerForm
from app.email_service import otp_send_response, send_otp_email, send_confirmation_email
from app.security import email_otp_verified, json_payload, mark_email_verified, save_resume

careers_bp = Blueprint("careers", __name__)

JOB_OPENINGS = [
    {
        "id":          "dev-fullstack",
        "title":       "Full Stack Developer",
        "department":  "Software Development",
        "location":    "Remote",
        "type":        "Full-time",
        "experience":  "2–5 Years",
        "icon":        "bi-code-slash",
        "description": "Build and maintain scalable web applications using Python/Django/Flask and React.",
        "requirements":["Python · Django / Flask", "React.js / Vue.js", "PostgreSQL / MySQL", "REST API design", "Git & CI/CD"],
    },
    {
        "id":          "dev-mobile",
        "title":       "Mobile App Developer",
        "department":  "Software Development",
        "location":    "Remote",
        "type":        "Full-time",
        "experience":  "1–3 Years",
        "icon":        "bi-phone",
        "description": "Design and develop cross-platform mobile apps for Android and iOS.",
        "requirements":["React Native or Flutter", "REST APIs & Firebase", "Android Studio / Xcode", "UX best practices"],
    },
    {
        "id":          "cloud-engineer",
        "title":       "Cloud & DevOps Engineer",
        "department":  "Infrastructure & Cloud",
        "location":    "Remote",
        "type":        "Full-time",
        "experience":  "2–4 Years",
        "icon":        "bi-cloud",
        "description": "Manage cloud infrastructure on AWS/Azure, implement CI/CD, and ensure uptime.",
        "requirements":["AWS / Azure / GCP", "Docker & Kubernetes", "Terraform / Ansible", "Linux SysAdmin"],
    },
    {
        "id":          "digital-marketing",
        "title":       "Digital Marketing Executive",
        "department":  "Marketing",
        "location":    "Remote",
        "type":        "Full-time",
        "experience":  "1–3 Years",
        "icon":        "bi-graph-up",
        "description": "Execute SEO, Google Ads, and social media campaigns that drive measurable growth.",
        "requirements":["SEO / SEM expertise", "Google Ads & Analytics", "Social media management", "Meta Ads"],
    },
    {
        "id":          "it-support",
        "title":       "IT Support Engineer",
        "department":  "Technical Support",
        "location":    "Remote",
        "type":        "Full-time",
        "experience":  "0–2 Years",
        "icon":        "bi-headset",
        "description": "Provide L1/L2 helpdesk and on-site technical support to clients across Bihar.",
        "requirements":["Windows / Linux basics", "Networking fundamentals", "Hardware troubleshooting", "Customer communication"],
    },
    {
        "id":          "bde",
        "title":       "Business Development Executive",
        "department":  "Sales & Business",
        "location":    "Remote",
        "type":        "Full-time",
        "experience":  "1–3 Years",
        "icon":        "bi-briefcase",
        "description": "Identify new business opportunities and manage client relationships in the IT sector.",
        "requirements":["B2B / B2C sales", "Strong communication", "IT product knowledge", "CRM tools"],
    },
]


# ── OTP Verification Routes ──
@careers_bp.route("/careers/send-otp", methods=["POST"])
@csrf.exempt
@limiter.limit("5 per hour")
def send_application_otp():
    """Send OTP to candidate before allowing application submission."""
    payload = json_payload()
    email = (payload.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400
    
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400
    
    try:
        otp_record = OTPVerification.create_otp(email, purpose="job_application")
        success = send_otp_email(email, otp_record.plain_otp, purpose="job application verification")
        return otp_send_response(success, otp_record.plain_otp)
            
    except Exception as e:
        current_app.logger.error(f"OTP send error: {e}")
        return jsonify({"success": False, "message": "An error occurred. Please try again."}), 500


@careers_bp.route("/careers/verify-otp", methods=["POST"])
@csrf.exempt
@limiter.limit("10 per minute")
def verify_application_otp():
    """Verify OTP before allowing application submission."""
    payload = json_payload()
    email = (payload.get("email") or "").strip().lower()
    otp = (payload.get("otp") or "").strip()
    
    if not email or not otp:
        return jsonify({"success": False, "message": "Email and OTP are required."}), 400
    
    is_valid = OTPVerification.verify_otp(email, otp, purpose="job_application")
    
    if is_valid:
        token = mark_email_verified(email, "job_application")
        return jsonify({
            "success": True,
            "message": "Email verified successfully!",
            "verification_token": token,
        })
    return jsonify({"success": False, "message": "Invalid or expired OTP. Please request a new one."}), 400


@careers_bp.route("/careers")
def careers():
    return render_template("careers.html", jobs=JOB_OPENINGS)


@careers_bp.route("/careers/apply", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per hour", methods=["POST"])
def apply():
    form = CareerForm()

    # Pre-select position from query param
    if request.method == "GET" and request.args.get("position"):
        form.position.data = request.args.get("position")

    if form.validate_on_submit():
        submit_email = bleach.clean(form.email.data, tags=[], strip=True)[:254].lower()
        if not email_otp_verified(submit_email, "job_application"):
            flash("Please verify your email with OTP before submitting.", "danger")
            return render_template("apply.html", form=form, jobs=JOB_OPENINGS)

        unique, upload_error = save_resume(form.resume.data)
        if upload_error:
            flash(upload_error, "danger")
            return render_template("apply.html", form=form, jobs=JOB_OPENINGS)

        application = JobApplication(
            full_name       = bleach.clean(form.full_name.data,    tags=[], strip=True)[:120],
            email           = bleach.clean(form.email.data,        tags=[], strip=True)[:254],
            phone           = bleach.clean(form.phone.data,        tags=[], strip=True)[:20],
            position        = bleach.clean(form.position.data,     tags=[], strip=True)[:200],
            experience      = bleach.clean(form.experience.data or "", tags=[], strip=True)[:50],
            cover_letter    = bleach.clean(form.cover_letter.data or "", tags=[], strip=True)[:3000],
            resume_filename = unique,
            ip_address      = request.remote_addr,
        )
        db.session.add(application)
        db.session.commit()

        # ── Send Confirmation Email ──
        try:
            send_confirmation_email(
                email=form.email.data,
                name=form.full_name.data,
                subject_line="Application Received - " + form.position.data,
                message=f"Position: {form.position.data}\nExperience: {form.experience.data or 'Not specified'}",
                template="application"
            )
        except Exception as e:
            current_app.logger.warning(f"Confirmation email failed: {e}")

        session.pop("otp_verified:job_application", None)
        flash(
            f"Application submitted for {form.position.data}. "
            "We'll review your profile and reach out within 5–7 business days.",
            "success"
        )
        return redirect(url_for("careers.careers"))

    return render_template("apply.html", form=form, jobs=JOB_OPENINGS)
