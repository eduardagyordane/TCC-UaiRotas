from uairotas.models import User


def test_password_is_hashed(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@example.invalid").first()

        assert user.password_hash != "senha-de-teste-sem-segredo"
        assert user.check_password("senha-de-teste-sem-segredo") is True
        assert user.check_password("outra-senha") is False
