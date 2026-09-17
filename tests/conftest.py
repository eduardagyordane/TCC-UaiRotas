import pytest

from uairotas import create_app
from uairotas.extensions import db
from uairotas.models import User


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False


@pytest.fixture()
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        admin = User(name="Admin UaiRotas", email="admin@uairotas.com", role="admin")
        admin.set_password("SenhaSegura123!")
        db.session.add(admin)
        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()

