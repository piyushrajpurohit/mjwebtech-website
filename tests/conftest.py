import os

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ["RATELIMIT_ENABLED"] = "false"

import pytest

from app import create_app, db


@pytest.fixture
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
