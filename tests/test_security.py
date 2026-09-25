from pathlib import Path
import sqlite3
import pytest
from conftest import TestConfig
from uairotas import create_app
from uairotas.extensions import db
from uairotas.models import User,SchemaMigration

@pytest.mark.parametrize("target",["https://example.invalid/x","//example.invalid/x",r"\\example.invalid/x","/\\example.invalid/x","/\n/evil"])
def test_hostile_next_rejected(client,target):
    response=client.post("/login",query_string={"next":target},data={"email":"admin@example.invalid","password":"senha-de-teste-sem-segredo"})
    assert response.status_code==302 and response.location=="/"

def test_rate_limit_and_generic_feedback(client):
    for _ in range(5):
        response=client.post("/login",data={"email":"admin@example.invalid","password":"wrong-password"})
        assert response.status_code==200 and b"wrong-password" not in response.data
    response=client.post("/login",data={"email":"admin@example.invalid","password":"senha-de-teste-sem-segredo"})
    assert response.status_code==429 and response.headers["Retry-After"]=="900"

def test_security_headers_csrf_expiry_and_upload_limit(app,authenticated):
    response=authenticated.get("/")
    assert response.headers["Cache-Control"]=="no-store" and response.headers["X-Frame-Options"]=="DENY"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    app.config["WTF_CSRF_ENABLED"]=True
    for path in ["/logout","/frota/registros/veiculo","/usuarios/novo","/perfil","/alertas/reconhecer"]:
        response=authenticated.post(path,data={})
        assert response.status_code==400 and b"formul" in response.data
    response=authenticated.post("/perfil",data=b"x"*(2*1024*1024+1),content_type="application/x-www-form-urlencoded")
    assert response.status_code==413

def test_production_requires_secret_hosts_and_secure_cookies():
    class Prod(TestConfig): APP_ENV="production"
    with pytest.raises(RuntimeError,match="SECRET_KEY"): create_app(Prod)
    Prod.SECRET_KEY="substitua-por-uma-chave-aleatoria-gerada-localmente"
    with pytest.raises(RuntimeError,match="SECRET_KEY"): create_app(Prod)
    Prod.SECRET_KEY="test-only-random-looking-key-"+"x"*40
    with pytest.raises(RuntimeError,match="TRUSTED_HOSTS"): create_app(Prod)
    Prod.TRUSTED_HOSTS=["example.invalid"]
    app=create_app(Prod)
    assert app.config["SESSION_COOKIE_SECURE"] and app.config["REMEMBER_COOKIE_SECURE"]
    response=app.test_client().get("/login",base_url="https://example.invalid")
    assert "Strict-Transport-Security" in response.headers
    assert app.test_client().get("/login",base_url="https://other.invalid").status_code==400

def test_backup_is_consistent_restorable_and_never_overwrites(app,tmp_path):
    output=tmp_path/"snapshot.db"
    result=app.test_cli_runner().invoke(args=["backup-db","--output",str(output)])
    assert result.exit_code==0,result.output
    original=output.read_bytes()
    with sqlite3.connect(output) as restored:
        assert restored.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        assert restored.execute("SELECT email FROM users").fetchone()[0]=="admin@example.invalid"
        assert restored.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()==[(1,),(2,)]
    second=app.test_cli_runner().invoke(args=["backup-db","--output",str(output)])
    assert second.exit_code!=0 and output.read_bytes()==original

def test_demo_cli_explicit_and_does_not_overwrite(app):
    runner=app.test_cli_runner()
    assert runner.invoke(args=["seed-demo"]).exit_code==0
    assert runner.invoke(args=["seed-demo"]).exit_code!=0
    app.config["APP_ENV"]="production"
    assert runner.invoke(args=["seed-demo"]).exit_code!=0

def test_no_default_admin_credentials_and_cli_validation(app):
    runner=app.test_cli_runner()
    assert runner.invoke(args=["create-admin","--name","A","--email","bad","--password","short"]).exit_code!=0
    assert runner.invoke(args=["create-admin","--name","Outro admin","--email","second@example.invalid","--password","test-password-long"]).exit_code==0
    assert runner.invoke(args=["create-admin","--name","Outro admin","--email","second@example.invalid","--password","test-password-long"]).exit_code!=0
