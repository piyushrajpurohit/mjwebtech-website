"""
email_service.py — MJ WebTech Email Service
Handles OTP generation, verification, and transactional emails.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from flask import current_app
from flask_mail import Message


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of specified length."""
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))


def generate_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def send_email(subject: str, recipients: list, body: str, html: str = None) -> bool:
    """
    Send an email via Flask-Mail.
    Returns True if successful, False otherwise.
    """
    try:
        from app import mail
        
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html
        )
        mail.send(msg)
        current_app.logger.info(f"Email sent successfully to {recipients}")
        return True
    except Exception as e:
        current_app.logger.error(f"Email sending failed: {e}")
        return False


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
    company_email = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@mjwebtech.com")
    
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
    company_website = current_app.config.get("COMPANY_WEBSITE", "https://mjwebtech.com")
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
            
            <a href="https://mjwebtech.com/careers" class="btn">View Open Positions</a>
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
            
            <p style="color: #64748b;">In the meantime, you can learn more about our services at <a href="https://mjwebtech.com/services">mjwebtech.com/services</a></p>
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
            <p>&copy; {datetime.now().year()} {company_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""