from pathlib import Path
from unittest.mock import patch

from app import db
from app.models import JobApplication, OTPVerification, User
from app.email_service import otp_send_response


def test_about_and_privacy_pages(client):
    assert client.get("/about").status_code == 200
    assert client.get("/privacy").status_code == 200


def test_cors_allows_custom_domain(client):
    response = client.get("/api/health", headers={"Origin": "https://mjwebtech.in"})
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "https://mjwebtech.in"


def test_health_503_when_db_down(client):
    with patch("app.routes.api.db.session.execute", side_effect=RuntimeError("db down")):
        response = client.get("/api/health")
    assert response.status_code == 503
    assert response.get_json()["database"] == "unavailable"


def test_register_without_otp_fails(client):
    response = client.post("/api/register", json={
        "name": "Test User",
        "email": "newuser@example.com",
        "password": "password123",
    })
    assert response.status_code == 403
    assert response.get_json()["error"] == "otp_required"


def test_contact_without_otp_fails(client):
    response = client.post("/api/contact", json={
        "name": "Test User",
        "email": "lead@example.com",
        "subject": "Hello there",
        "message": "This message is long enough to pass validation.",
    })
    assert response.status_code == 403
    assert response.get_json()["error"] == "otp_required"


def test_register_succeeds_with_otp_token(client, app):
    with app.app_context():
        record = OTPVerification.create_otp("ok@example.com", "registration")
        code = record.plain_otp

    verify = client.post("/api/auth/verify-otp", json={
        "email": "ok@example.com",
        "otp": code,
    })
    assert verify.status_code == 200
    token = verify.get_json()["verification_token"]

    other = app.test_client()
    created = other.post("/api/register", json={
        "name": "Ok User",
        "email": "ok@example.com",
        "password": "password123",
        "verification_token": token,
    })
    assert created.status_code == 201
    assert created.get_json()["success"] is True


def test_production_otp_json_omits_code(app):
    with app.app_context():
        with patch("app.email_service._local_otp_fallback_allowed", return_value=False):
            payload, status = otp_send_response(True, "123456")
            data = payload.get_json()
            assert status == 200
            assert "otp" not in data

            payload, status = otp_send_response(False, "123456")
            data = payload.get_json()
            assert status == 503
            assert "otp" not in data


def test_otp_is_hashed_and_old_codes_invalidated(app):
    with app.app_context():
        first = OTPVerification.create_otp("hash@example.com", "registration")
        first_code = first.plain_otp
        assert first.otp != first_code
        assert len(first.otp) > 6

        second = OTPVerification.create_otp("hash@example.com", "registration")
        assert OTPVerification.verify_otp("hash@example.com", first_code, "registration") is False
        assert OTPVerification.verify_otp("hash@example.com", second.plain_otp, "registration") is True


def test_inactive_user_cannot_login(client, app):
    with app.app_context():
        user = User(name="Inactive", email="inactive@example.com", is_active=False)
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

    response = client.post("/api/login", json={
        "email": "inactive@example.com",
        "password": "password123",
    })
    assert response.status_code == 401


def test_resume_is_not_public(client, app):
    upload = Path(app.config["UPLOAD_FOLDER"])
    upload.mkdir(parents=True, exist_ok=True)
    filename = "secret-resume.pdf"
    (upload / filename).write_bytes(b"%PDF-1.4 test")

    with app.app_context():
        application = JobApplication(
            full_name="Candidate",
            email="candidate@example.com",
            phone="9876543210",
            position="Full Stack Developer",
            resume_filename=filename,
        )
        db.session.add(application)
        db.session.commit()
        application_id = application.id

    public = client.get(f"/static/uploads/{filename}")
    assert public.status_code == 404

    unauthenticated = client.get(f"/admin/applications/{application_id}/resume")
    assert unauthenticated.status_code in (302, 401)
