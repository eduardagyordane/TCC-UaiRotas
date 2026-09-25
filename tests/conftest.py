import pytest
from uairotas import create_app
from uairotas.extensions import db
from uairotas.migrations import migrate
from uairotas.models import User

class TestConfig:
    TESTING = True
    APP_ENV = "development"
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    MAPBOX_ACCESS_TOKEN = "pk.test-mapbox-token"
    TRUSTED_HOSTS = None
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        migrate()
        admin = User(name="Admin UaiRotas", email="admin@example.invalid", role="admin")
        admin.set_password("senha-de-teste-sem-segredo")
        db.session.add(admin)
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def authenticated(client):
    with client.session_transaction() as session:
        session["_user_id"] = "1:1"
        session["_fresh"] = True
    return client

@pytest.fixture()
def demo(app):
    from uairotas.demo import seed_demo
    with app.app_context():
        seed_demo()

def synthetic_cpf(seed=900000001):
    digits = [int(x) for x in str(seed)]
    for length in (9, 10):
        digits.append((sum(n * (length + 1 - i) for i, n in enumerate(digits)) * 10 % 11) % 10)
    return "".join(map(str, digits))
