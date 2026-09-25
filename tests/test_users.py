from datetime import date
import pytest
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError
from conftest import synthetic_cpf
from uairotas.extensions import db
from uairotas.migrations import migrate
from uairotas.models import User

def user_data(**overrides):
    values=dict(name="Usuário fictício",phone="(11) 99999-0001",email="usuario@example.invalid",
                address="Endereço de teste reservado",cpf=synthetic_cpf(),birth_date="1992-05-18",
                role="supervisor",password="senha-de-teste-123",active="on")
    values.update(overrides);return values

def test_create_edit_all_fields_and_json(app, authenticated):
    assert authenticated.post("/usuarios/novo",data=user_data()).status_code==302
    with app.app_context():
        user=User.query.filter_by(email="usuario@example.invalid").one()
        assert user.phone=="11999990001" and user.cpf==synthetic_cpf() and user.check_password("senha-de-teste-123")
        old_hash=user.password_hash
    data=user_data(name="Nome atualizado",phone="(34) 99999-0002",email="new@example.invalid",address="Novo endereço",
        cpf=synthetic_cpf(900000002),birth_date="1990-10-22",role="admin",password="")
    response=authenticated.post("/usuarios/2/editar?busca=Nome&pagina=1",data=data)
    assert response.status_code==302 and "busca=Nome" in response.location
    with app.app_context():
        user=db.session.get(User,2)
        assert user.name=="Nome atualizado" and user.phone=="34999990002" and user.email=="new@example.invalid"
        assert user.address=="Novo endereço" and user.cpf==data["cpf"] and user.birth_date==date(1990,10,22)
        assert user.role=="admin" and user.password_hash==old_hash and user.auth_version==2
    detail=authenticated.get("/usuarios/2/dados").json
    assert detail["address"]=="Novo endereço" and "password_hash" not in detail

@pytest.mark.parametrize("field,value",[("email","bad"),("phone","abc"),("phone","11"),("cpf","abc"),("cpf","11111111111"),
    ("birth_date","2999-01-01"),("birth_date","bad"),("role","owner"),("password","short"),("name","x"*121),("name","")])
def test_invalid_values_not_saved_or_password_repopulated(app,authenticated,field,value):
    response=authenticated.post("/usuarios/novo",data=user_data(**{field:value}))
    assert response.status_code==422 and b"data-auto-open" in response.data
    assert b'value="senha-de-teste-123"' not in response.data
    with app.app_context(): assert User.query.count()==1

def test_duplicates(app,authenticated):
    authenticated.post("/usuarios/novo",data=user_data())
    assert authenticated.post("/usuarios/novo",data=user_data(cpf=synthetic_cpf(900000002))).status_code==422
    assert authenticated.post("/usuarios/novo",data=user_data(email="other@example.invalid")).status_code==422
    with app.app_context(): assert User.query.count()==2

def test_last_admin_guard_in_http_and_database(app,authenticated):
    response=authenticated.post("/usuarios/1/editar",data=user_data(name="Admin UaiRotas",email="admin@example.invalid",password=""))
    assert response.status_code==422 and "administrador ativo".encode() in response.data
    with app.app_context():
        for sql in ["UPDATE users SET role='supervisor' WHERE id=1","UPDATE users SET active=0 WHERE id=1","DELETE FROM users WHERE id=1"]:
            with pytest.raises(IntegrityError): db.session.execute(text(sql));db.session.commit()
            db.session.rollback()
        assert db.session.get(User,1).role=="admin"

def test_supervisor_permissions_and_private_details(app,authenticated):
    authenticated.post("/usuarios/novo",data=user_data())
    with authenticated.session_transaction() as s:s["_user_id"]="2:1"
    for path in ["/usuarios","/usuarios/1/dados","/motoristas/1/foto","/frota/cadastros/veiculo/1/editar"]:
        assert authenticated.get(path).status_code==403
    assert authenticated.post("/frota/registros/veiculo",data={}).status_code==403
    assert authenticated.post("/usuarios/novo",data=user_data()).status_code==403
    for path in ["/","/rotas","/frota","/relatorios","/perfil"]: assert authenticated.get(path).status_code==200
    assert b'href="/usuarios"' not in authenticated.get("/").data

def test_pagination_keeps_one_dialog_and_masks_private_data(app,authenticated):
    with app.app_context():
        hash=db.session.get(User,1).password_hash
        db.session.add_all(User(name=f"Teste {i:04d}",email=f"t{i}@example.invalid",role="supervisor",cpf=synthetic_cpf(900000100+i),
            address="ENDERECO_NAO_LISTAR",birth_date=date(1993,1,1),password_hash=hash) for i in range(1000))
        db.session.commit()
    response=authenticated.get("/usuarios")
    assert response.status_code==200 and len(response.data)<50000
    assert response.data.count(b"data-user-edit=")==25 and response.data.count(b'id="user-dialog"')==1
    assert b"ENDERECO_NAO_LISTAR" not in response.data and synthetic_cpf(900000100).encode() not in response.data
    assert b"1993-01-01" not in response.data
    assert authenticated.get("/usuarios?pagina=2").data != response.data

@pytest.mark.parametrize("search",["fictício","usuario@example.invalid","900.000"])
def test_search_name_email_cpf(authenticated,search):
    authenticated.post("/usuarios/novo",data=user_data())
    assert "Usuário fictício".encode() in authenticated.get("/usuarios",query_string={"busca":search}).data

def test_password_change_revokes_session_and_remember_cookie(app,authenticated):
    authenticated.post("/usuarios/novo",data=user_data())
    other=app.test_client()
    assert other.post("/login",data={"email":"usuario@example.invalid","password":"senha-de-teste-123","remember":"on"}).status_code==302
    assert other.get("/perfil").status_code==200
    authenticated.post("/usuarios/2/editar",data=user_data(password="senha-nova-de-teste"))
    assert other.get("/perfil").status_code==302
    with other.session_transaction() as s:s.clear()
    assert other.get("/perfil").status_code==302
    assert other.post("/login",data={"email":"usuario@example.invalid","password":"senha-nova-de-teste"}).status_code==302
    assert other.get("/perfil").status_code==200

def test_profile_requires_current_password_for_email_or_password(app,authenticated):
    values={"name":"Admin atualizado","email":"admin@example.invalid","password":"nova-senha-123","password_confirmation":"nova-senha-123"}
    assert authenticated.post("/perfil",data=values).status_code==422
    values["current_password"]="senha-de-teste-sem-segredo"
    assert authenticated.post("/perfil",data=values).status_code==302
    with app.app_context():
        user=db.session.get(User,1)
        assert user.name=="Admin atualizado" and user.check_password("nova-senha-123") and user.auth_version==2
    assert authenticated.get("/perfil").status_code==200

def test_legacy_migration_preserves_user_and_is_idempotent(app):
    with app.app_context():
        old_hash=db.session.get(User,1).password_hash
        db.drop_all()
        db.session.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY,name VARCHAR(120) NOT NULL,email VARCHAR(255) UNIQUE NOT NULL,password_hash VARCHAR(255) NOT NULL,role VARCHAR(20) NOT NULL,active BOOLEAN NOT NULL,created_at DATETIME NOT NULL)"))
        db.session.execute(text("INSERT INTO users VALUES(1,'Original','old@example.invalid',:hash,'admin',1,'2026-01-01')"),{"hash":old_hash})
        db.session.commit();migrate();migrate()
        columns={c["name"] for c in inspect(db.engine).get_columns("users")}
        assert {"phone","cpf","birth_date","address","auth_version"} <= columns
        db.session.expire_all()
        assert db.session.get(User,1).name=="Original" and db.session.get(User,1).password_hash==old_hash
