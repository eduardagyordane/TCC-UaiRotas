from uairotas.models import User


def test_password_is_hashed(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@uairotas.com").first()

        assert user.password_hash != "SenhaSegura123!"
        assert user.check_password("SenhaSegura123!") is True
        assert user.check_password("outra-senha") is False

