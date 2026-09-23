from datetime import date
import secrets

import pytest
from sqlalchemy import inspect, text

from uairotas.extensions import db
from uairotas.models import User


TEST_CPF_A = "0" * 11
TEST_CPF_B = "1" * 11
TEST_CPF_C = "2" * 11


def authenticate(client, user_id=1):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True


def valid_user_data(**overrides):
    data = {
        "name": "Usuário Fictício",
        "phone": "telefone-ficticio-a",
        "email": "usuario@example.invalid",
        "address": "Endereço fictício para teste",
        "cpf": TEST_CPF_A,
        "birth_date": "1992-05-18",
        "role": "supervisor",
        "password": secrets.token_urlsafe(16),
        "active": "on",
    }
    data.update(overrides)
    return data


def test_users_requires_authentication(client):
    response = client.get("/usuarios", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_supervisor_cannot_access_user_management(app, client):
    with app.app_context():
        supervisor = User(name="Supervisor Fictício", email="supervisor@example.invalid", role="supervisor")
        supervisor.set_password(secrets.token_urlsafe(16))
        db.session.add(supervisor)
        db.session.commit()
        supervisor_id = supervisor.id

    authenticate(client, supervisor_id)
    home_response = client.get("/")
    response = client.get("/usuarios")

    assert b'href="/usuarios"' not in home_response.data
    assert response.status_code == 403


def test_users_page_renders_summary_and_required_fields(client):
    authenticate(client)
    response = client.get("/usuarios")

    assert response.status_code == 200
    assert b"Admin UaiRotas" in response.data
    assert "Total de usuários".encode() in response.data
    assert "Administradores".encode() in response.data
    assert b' name="phone"' in response.data
    assert b' name="email"' in response.data
    assert b' name="address"' in response.data
    assert b' name="cpf"' in response.data
    assert b' name="birth_date"' in response.data
    assert b' name="role"' in response.data


def test_admin_can_create_user_with_all_fields(app, client):
    authenticate(client)
    payload = valid_user_data()
    response = client.post("/usuarios/novo", data=payload, follow_redirects=True)

    assert response.status_code == 200
    assert "Usuário cadastrado com sucesso.".encode() in response.data
    with app.app_context():
        user = User.query.filter_by(email="usuario@example.invalid").one()
        assert user.name == "Usuário Fictício"
        assert user.phone == "telefone-ficticio-a"
        assert user.address == "Endereço fictício para teste"
        assert user.cpf == TEST_CPF_A
        assert user.birth_date == date(1992, 5, 18)
        assert user.role == "supervisor"
        assert user.active is True
        assert user.check_password(payload["password"]) is True


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"cpf": "123"}, "Informe um CPF com 11 dígitos."),
        ({"birth_date": "data-inválida"}, "Preencha todos os campos obrigatórios."),
        ({"role": "operador"}, "Selecione uma função válida."),
        ({"password": "short"}, "A senha deve possuir pelo menos 8 caracteres."),
    ],
)
def test_create_user_validates_input(app, client, overrides, message):
    authenticate(client)
    response = client.post(
        "/usuarios/novo",
        data=valid_user_data(**overrides),
        follow_redirects=True,
    )

    assert message.encode() in response.data
    with app.app_context():
        assert User.query.filter_by(email="usuario@example.invalid").first() is None


def test_create_user_rejects_duplicate_email_and_cpf(app, client):
    authenticate(client)
    client.post("/usuarios/novo", data=valid_user_data())

    duplicate_email = client.post(
        "/usuarios/novo",
        data=valid_user_data(cpf=TEST_CPF_B),
        follow_redirects=True,
    )
    duplicate_cpf = client.post(
        "/usuarios/novo",
        data=valid_user_data(email="outro@example.invalid"),
        follow_redirects=True,
    )

    assert "Já existe um usuário com esse e-mail.".encode() in duplicate_email.data
    assert "Já existe um usuário com esse CPF.".encode() in duplicate_cpf.data


def test_admin_can_edit_every_user_field_without_changing_password(app, client):
    authenticate(client)
    client.post("/usuarios/novo", data=valid_user_data())
    with app.app_context():
        user = User.query.filter_by(email="usuario@example.invalid").one()
        user_id = user.id
        old_password_hash = user.password_hash

    response = client.post(
        f"/usuarios/{user_id}/editar",
        data=valid_user_data(
            name="Usuário Atualizado",
            phone="telefone-ficticio-b",
            email="atualizado@example.invalid",
            address="Segundo endereço fictício",
            cpf=TEST_CPF_B,
            birth_date="1990-10-22",
            role="admin",
            password="",
        ),
        follow_redirects=True,
    )

    assert "Usuário atualizado com sucesso.".encode() in response.data
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.name == "Usuário Atualizado"
        assert user.phone == "telefone-ficticio-b"
        assert user.email == "atualizado@example.invalid"
        assert user.address == "Segundo endereço fictício"
        assert user.cpf == TEST_CPF_B
        assert user.birth_date == date(1990, 10, 22)
        assert user.role == "admin"
        assert user.password_hash == old_password_hash


def test_admin_can_change_another_users_password(app, client):
    authenticate(client)
    client.post("/usuarios/novo", data=valid_user_data())
    with app.app_context():
        user_id = User.query.filter_by(email="usuario@example.invalid").one().id

    new_password = secrets.token_urlsafe(18)

    client.post(
        f"/usuarios/{user_id}/editar",
        data=valid_user_data(password=new_password),
    )

    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.check_password(new_password) is True


def test_admin_cannot_deactivate_own_account(app, client):
    authenticate(client)
    with app.app_context():
        admin = User.query.filter_by(email="admin@example.invalid").one()
        admin_id = admin.id

    payload = valid_user_data(
        name="Admin UaiRotas",
        email="admin@example.invalid",
        cpf=TEST_CPF_C,
        role="admin",
        password="",
    )
    payload.pop("active")
    response = client.post(
        f"/usuarios/{admin_id}/editar",
        data=payload,
        follow_redirects=True,
    )

    assert "Você não pode desativar o próprio usuário.".encode() in response.data
    with app.app_context():
        assert db.session.get(User, admin_id).active is True


def test_users_searches_by_name_email_and_cpf(client):
    authenticate(client)
    client.post("/usuarios/novo", data=valid_user_data())

    by_name = client.get("/usuarios?busca=Usu%C3%A1rio")
    by_email = client.get("/usuarios?busca=usuario%40example.invalid")
    by_cpf = client.get("/usuarios?busca=000.000")
    missing = client.get("/usuarios?busca=Inexistente")

    assert "Usuário Fictício".encode() in by_name.data
    assert "Usuário Fictício".encode() in by_email.data
    assert "Usuário Fictício".encode() in by_cpf.data
    assert "Nenhum usuário encontrado".encode() in missing.data


def test_main_navigation_links_to_users(client):
    authenticate(client)
    response = client.get("/")

    assert b'href="/usuarios"' in response.data


def test_init_db_upgrades_legacy_users_table(app):
    with app.app_context():
        db.drop_all()
        db.session.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    active BOOLEAN NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )
        )
        db.session.commit()

    result = app.test_cli_runner().invoke(args=["init-db"])

    assert result.exit_code == 0
    with app.app_context():
        columns = {column["name"] for column in inspect(db.engine).get_columns("users")}
        assert {"phone", "address", "cpf", "birth_date"}.issubset(columns)
