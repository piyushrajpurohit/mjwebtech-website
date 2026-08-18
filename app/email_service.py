"""
email_service.py — MJ WebTech Email Service
Handles OTP generation, verification, and transactional emails.
"""

import json
import secrets
import smtplib
import socket
import string
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from typing import Optional

from flask import current_app

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of specified length."""
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def mail_sender():
    """From address as (name, email).

    Brevo SMTP login (xxx@smtp-brevo.com) is an auth identity, not a sender.
    Always send as the verified MAIL_DEFAULT_SENDER instead.
    """
    configured = current_app.config.get("MAIL_DEFAULT_SENDER") or "noreply@mjwebtech.in"
    company = current_app.config.get("COMPANY_NAME", "MJ WebTech Pvt. Ltd.")
    if isinstance(configured, (tuple, list)) and len(configured) == 2:
        return (configured[0], configured[1])
    sender = str(configured).strip()
    return sender if "<" in sender and ">" in sender else (company, sender)


def sender_name_email() -> tuple[str, str]:
    sender = mail_sender()
    company = current_app.config.get("COMPANY_NAME", "MJ WebTech Pvt. Ltd.")
    if isinstance(sender, tuple):
        name, email = sender[0], sender[1]
    else:
        name, email = parseaddr(str(sender))
        if not email:
            email = str(sender).strip()
            name = company
    return (name or company, email)


def _brevo_api_key() -> str:
    key = (current_app.config.get("BREVO_API_KEY") or "").strip()
    if key:
        return key
    password = (current_app.config.get("MAIL_PASSWORD") or "").strip()
    # Brevo v3 API keys start with this prefix; SMTP keys do not.
    if password.startswith("xkeysib-"):
        return password
    return ""


def send_email(subject: str, recipients: list, body: str, html: str = None) -> bool:
    """Send email via Brevo HTTPS API, with timed SMTP only as a local fallback."""
    recipients = [str(r).strip() for r in (recipients or []) if str(r).strip()]
    if not recipients:
        current_app.logger.error("Email not sent: no recipients")
        return False

    sender_name, sender_email = sender_name_email()
    if "@smtp-brevo.com" in sender_email.lower() or sender_email.lower() == "smtp-relay.brevo.com":
        current_app.logger.error(
            "MAIL_DEFAULT_SENDER must be a verified sender in Brevo "
            "(for example noreply@mjwebtech.in), not the SMTP login."
        )
        return False

    api_key = _brevo_api_key()
    if api_key:
        return _send_via_brevo_api(
            api_key, sender_name, sender_email, recipients, subject, body, html
        )

    username = (current_app.config.get("MAIL_USERNAME") or "").strip()
    password = (current_app.config.get("MAIL_PASSWORD") or "").strip()
    if not username or not password:
        current_app.logger.error(
            "Email not sent: set BREVO_API_KEY on Render. SMTP ports 587/465 "
            "are blocked or delayed on Render, so OTP requests hang and mail "
            "never leaves the server."
        )
        return False

    current_app.logger.warning(
        "BREVO_API_KEY is not set; using SMTP with a short timeout. "
        "This often fails on Render — add a Brevo API key for production."
    )
    return _send_via_smtp(sender_name, sender_email, recipients, subject, body, html)


def _send_via_brevo_api(
    api_key: str,
    sender_name: str,
    sender_email: str,
    recipients: list,
    subject: str,
    body: str,
    html: str | None,
) -> bool:
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": email} for email in recipients],
        "subject": subject,
        "textContent": body or "",
        "htmlContent": html or f"<pre>{body or ''}</pre>",
    }
    request = urllib.request.Request(
        BREVO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )
    timeout = current_app.config.get("MAIL_TIMEOUT", 8)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            current_app.logger.info(
                "Brevo API accepted email to %s (HTTP %s)", recipients, status
            )
            return 200 <= int(status) < 300
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        current_app.logger.error("Brevo API HTTP %s from=%s: %s", exc.code, sender_email, detail)
        return False
    except Exception as exc:
        current_app.logger.error("Brevo API request failed: %s", exc)
        return False


def _send_via_smtp(
    sender_name: str,
    sender_email: str,
    recipients: list,
    subject: str,
    body: str,
    html: str | None,
) -> bool:
    username = (current_app.config.get("MAIL_USERNAME") or "").strip()
    password = (current_app.config.get("MAIL_PASSWORD") or "").strip()
    server = current_app.config.get("MAIL_SERVER", "smtp-relay.brevo.com")
    port = int(current_app.config.get("MAIL_PORT", 587))
    use_tls = current_app.config.get("MAIL_USE_TLS", True)
    use_ssl = current_app.config.get("MAIL_USE_SSL", False)
    timeout = int(current_app.config.get("MAIL_TIMEOUT", 8))

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = formataddr((sender_name, sender_email))
    message["To"] = ", ".join(recipients)
    if body:
        message.attach(MIMEText(body, "plain", "utf-8"))
    if html:
        message.attach(MIMEText(html, "html", "utf-8"))

    smtp = None
    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=timeout)
        else:
            smtp = smtplib.SMTP(server, port, timeout=timeout)
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
        smtp.login(username, password)
        smtp.sendmail(sender_email, recipients, message.as_string())
        current_app.logger.info("Email sent via SMTP %s:%s to %s", server, port, recipients)
        return True
    except (smtplib.SMTPException, socket.timeout, TimeoutError, OSError) as exc:
        current_app.logger.error(
            "SMTP send failed via %s:%s login=%s from=%s: %s",
            server,
            port,
            username,
            sender_email,
            exc,
        )
        return False
    finally:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:
                pass


def otp_send_response(success: bool, otp: str, resent: bool = False):
    """JSON payload for OTP send endpoints. Never return the OTP in production."""
    from flask import jsonify

    if success:
        message = (
            "New OTP sent! Check your email."
            if resent
            else "OTP sent! Check your email for the verification code."
        )
        return jsonify({
            "success": True,
            "message": message,
            "expires_in": 600,
        }), 200

    current_app.logger.warning("OTP email was not delivered")
    if current_app.debug:
        current_app.logger.warning("DEBUG OTP (not emailed): %s", otp)
        return jsonify({
            "success": True,
            "message": (
                "OTP generated successfully. For local development, use the "
                "code from the server logs if email delivery is unavailable."
            ),
            "expires_in": 600,
            "otp": otp,
        }), 200

    return jsonify({
        "success": False,
        "message": (
            "We could not send the verification email. Please try again in a "
            "few minutes, and check that the address is correct."
        ),
    }), 503


def send_otp_email(email: str, otp: str, purpose: str = "verification") -> bool:
    """
    Send OTP email to user for verification.
    
    Args:
        email: Recipient email address
        otp: One-time password to send
        purpose: Purpose of OTP (verification, password_reset, etc.)
    
    Returns:
        bool: True if email sent successfully
    """
    company_name = current_app.config.get("COMPANY_NAME", "MJ WebTech Pvt. Ltd.")
    company_email = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@mjwebtech.in")
    
    subject = f"[{company_name}] Your OTP for {purpose.replace('_', ' ').title()}"
    
    body = f"""
Dear User,

Your One-Time Password (OTP) for {purpose.replace('_', ' ').title()} is:

    {otp}

This OTP is valid for 10 minutes. Please do not share this OTP with anyone.

If you did not request this, please ignore this email.

Best regards,
{company_name}
"""
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 30px; text-align: center; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
        .content {{ padding: 30px; }}
        .otp-box {{ background: #f8fafc; border: 2px dashed #6366f1; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
        .otp-code {{ font-size: 32px; font-weight: bold; color: #6366f1; letter-spacing: 8px; }}
        .footer {{ background: #1e293b; padding: 20px; text-align: center; color: #94a3b8; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{company_name}</h1>
        </div>
        <div class="content">
            <h2 style="color: #1e293b; margin-top: 0;">OTP Verification</h2>
            <p style="color: #64748b;">Your One-Time Password for <strong>{purpose.replace('_', ' ').title()}</strong> is:</p>
            <div class="otp-box">
                <div class="otp-code">{otp}</div>
            </div>
            <p style="color: #64748b; font-size: 14px;">This OTP is valid for <strong>10 minutes</strong>.</p>
            <p style="color: #94a3b8; font-size: 12px;">If you didn't request this, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    
    return send_email(subject, [email], body, html)


def send_confirmation_email(
    email: str,
    name: str,
    subject_line: str,
    message: str,
    template: str = "general"
) -> bool:
    """
    Send confirmation email after form submission.
    
    Args:
        email: Recipient email
        name: Recipient name
        subject_line: Subject of the confirmation
        message: Custom message body
        template: Type of confirmation (general, application, contact)
    
    Returns:
        bool: True if email sent successfully
    """
    company_name = current_app.config.get("COMPANY_NAME", "MJ WebTech Pvt. Ltd.")
    company_website = current_app.config.get("COMPANY_WEBSITE", "https://mjwebtech.in")
    company_phone = current_app.config.get("COMPANY_PHONE", "+91-98765-43210")
    
    subject = f"[{company_name}] {subject_line}"
    
    if template == "application":
        body = f"""
Dear {name},

Thank you for applying for the position! We have received your application successfully.

What happens next?
- Our HR team will review your application within 2-3 business days
- If your profile matches our requirements, we will schedule an interview
- You will receive an email with further instructions

Application Details:
{message}

Best regards,
HR Team
{company_name}
"""
        html = _get_application_confirmation_html(company_name, name, message)
        
    elif template == "contact":
        body = f"""
Dear {name},

Thank you for contacting us! We have received your message and will get back to you within 24 hours.

Your Message:
{message}

Best regards,
{company_name}
"""
        html = _get_contact_confirmation_html(company_name, name, message)
        
    else:
        body = f"""
Dear {name},

Thank you! Your submission has been received successfully.

{message}

Best regards,
{company_name}
"""
        html = _get_general_confirmation_html(company_name, name, message)
    
    return send_email(subject, [email], body, html)


def _get_application_confirmation_html(company_name: str, name: str, details: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px; text-align: center; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; }}
        .check-icon {{ font-size: 48px; margin-bottom: 10px; }}
        .content {{ padding: 40px; }}
        .content h2 {{ color: #1e293b; margin-top: 0; }}
        .details-box {{ background: #f8fafc; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .footer {{ background: #1e293b; padding: 30px; text-align: center; color: #94a3b8; font-size: 12px; }}
        .btn {{ display: inline-block; background: #6366f1; color: #ffffff; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="check-icon">✓</div>
            <h1>Application Received!</h1>
        </div>
        <div class="content">
            <h2>Dear {name},</h2>
            <p>Thank you for applying! We have received your application successfully.</p>
            
            <div class="details-box">
                <strong>What's Next?</strong>
                <ul style="color: #64748b; margin-top: 10px;">
                    <li>Our HR team will review your application within 2-3 business days</li>
                    <li>If your profile matches our requirements, we will schedule an interview</li>
                    <li>You will receive an email with further instructions</li>
                </ul>
            </div>
            
            <p style="color: #64748b;">If you have any questions, feel free to reach out to us.</p>
            
            <a href="https://mjwebtech.in/careers" class="btn">View Open Positions</a>
        </div>
        <div class="footer">
            <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""


def _get_contact_confirmation_html(company_name: str, name: str, message: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 40px; text-align: center; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; }}
        .content {{ padding: 40px; }}
        .content h2 {{ color: #1e293b; margin-top: 0; }}
        .message-box {{ background: #f8fafc; border-left: 4px solid #6366f1; padding: 20px; margin: 20px 0; }}
        .footer {{ background: #1e293b; padding: 30px; text-align: center; color: #94a3b8; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Message Received!</h1>
        </div>
        <div class="content">
            <h2>Dear {name},</h2>
            <p>Thank you for contacting us! We have received your message and will get back to you within <strong>24 hours</strong>.</p>
            
            <div class="message-box">
                <strong>Your Message:</strong>
                <p style="color: #64748b; margin-top: 10px;">{message[:200]}...</p>
            </div>
            
            <p style="color: #64748b;">In the meantime, you can learn more about our services at <a href="https://mjwebtech.in/services">mjwebtech.in/services</a></p>
        </div>
        <div class="footer">
            <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""


def _get_general_confirmation_html(company_name: str, name: str, message: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 40px; text-align: center; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; }}
        .content {{ padding: 40px; }}
        .content h2 {{ color: #1e293b; margin-top: 0; }}
        .footer {{ background: #1e293b; padding: 30px; text-align: center; color: #94a3b8; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Thank You!</h1>
        </div>
        <div class="content">
            <h2>Dear {name},</h2>
            <p>{message}</p>
            <p style="color: #64748b;">We appreciate your interest in {company_name}.</p>
        </div>
        <div class="footer">
            <p>&copy; {datetime.now().year} {company_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""