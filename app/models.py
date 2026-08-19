"""
app/models.py — SQLAlchemy ORM models.
Tables: contacts, job_applications
Structured so SQLite (dev) and MySQL (production) both work transparently.
"""

from datetime import datetime, timedelta
from hmac import compare_digest
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """Stores user accounts for API authentication."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(30), default="user")

    def __repr__(self):
        return f"<User {self.id} — {self.email}>"

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class ApiItem(db.Model):
    """Simple item model used by the JSON API demo endpoints."""
    __tablename__ = "api_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ApiItem {self.id} — {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


class Contact(db.Model):
    """Stores contact-form submissions."""
    __tablename__ = "contacts"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(200), nullable=False)
    company    = db.Column(db.String(200), nullable=True)
    phone      = db.Column(db.String(20),  nullable=True)
    subject    = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text,        nullable=False)
    ip_address = db.Column(db.String(45),  nullable=True)   # IPv6-safe length
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)
    is_read    = db.Column(db.Boolean,     default=False)
    status     = db.Column(db.String(30),  default="New")

    def __repr__(self):
        return f"<Contact {self.id} — {self.name}>"

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "company":    self.company,
            "phone":      self.phone,
            "subject":    self.subject,
            "message":    self.message,
            "status":     self.status,
            "created_at": self.created_at.isoformat(),
        }

    action_logs = db.relationship(
        "ContactActionLog",
        back_populates="contact",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ContactActionLog(db.Model):
    """Records admin actions taken on contact inquiries."""
    __tablename__ = "contact_action_logs"

    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    action = db.Column(db.String(120), nullable=False)
    performed_by = db.Column(db.String(200), nullable=False)
    performed_by_id = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contact = db.relationship("Contact", back_populates="action_logs")

    def __repr__(self):
        return f"<ContactActionLog {self.id} — {self.action} by {self.performed_by}>"


class JobApplication(db.Model):
    """Stores career / job-application submissions."""
    __tablename__ = "job_applications"

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(200), nullable=False)
    phone         = db.Column(db.String(20),  nullable=False)
    position      = db.Column(db.String(200), nullable=False)
    experience    = db.Column(db.String(50),  nullable=True)
    cover_letter  = db.Column(db.Text,        nullable=True)
    resume_filename = db.Column(db.String(300), nullable=True)   # stored filename
    ip_address    = db.Column(db.String(45),  nullable=True)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    status        = db.Column(db.String(30),  default="pending")  # pending/reviewed/shortlisted/rejected

    def __repr__(self):
        return f"<JobApplication {self.id} — {self.full_name} for {self.position}>"


class OTPVerification(db.Model):
    """Stores OTP verification codes for registration and password reset."""
    __tablename__ = "otp_verifications"

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(200), nullable=False, index=True)
    otp        = db.Column(db.String(255), nullable=False)
    purpose    = db.Column(db.String(50), nullable=False)  # registration, password_reset, email_verify
    is_used    = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<OTPVerification {self.email} — {self.purpose}>"

    def is_valid(self) -> bool:
        """Check if OTP is still valid (not expired and not used)."""
        return not self.is_used and datetime.utcnow() < self.expires_at

    @staticmethod
    def _otp_matches(stored: str, provided: str) -> bool:
        if not stored or not provided:
            return False
        if stored.startswith(("pbkdf2:", "scrypt:", "argon2:")):
            return check_password_hash(stored, provided)
        return compare_digest(stored, provided)

    @staticmethod
    def create_otp(email: str, purpose: str = "registration", expiry_minutes: int = 10) -> "OTPVerification":
        """Create a new OTP. Previous unused codes for this email+purpose are invalidated."""
        from app.email_service import generate_otp

        OTPVerification.query.filter_by(
            email=email,
            purpose=purpose,
            is_used=False,
        ).update({OTPVerification.is_used: True}, synchronize_session=False)

        plaintext = generate_otp(6)
        expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
        otp_record = OTPVerification(
            email=email,
            otp=generate_password_hash(plaintext),
            purpose=purpose,
            expires_at=expires_at,
        )
        otp_record.plain_otp = plaintext
        db.session.add(otp_record)
        db.session.commit()
        return otp_record

    @staticmethod
    def verify_otp(email: str, otp: str, purpose: str = "registration") -> bool:
        """
        Verify an OTP code.
        Returns True if valid, False otherwise.
        Marks OTP as used after successful verification.
        """
        records = OTPVerification.query.filter_by(
            email=email,
            purpose=purpose,
            is_used=False,
        ).order_by(OTPVerification.created_at.desc()).all()

        for otp_record in records:
            if otp_record.is_valid() and OTPVerification._otp_matches(otp_record.otp, otp):
                otp_record.is_used = True
                db.session.commit()
                return True
        return False
