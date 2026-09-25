import os
import sqlite3
from pathlib import Path
from zoneinfo import ZoneInfo

import click
from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFError
from sqlalchemy import event
from werkzeug.exceptions import SecurityError

from .config import Config
from .extensions import csrf, db, login_manager


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    app.config.from_object(config_object)
    ZoneInfo(app.config["TIMEZONE"])
    if app.config["APP_ENV"] == "production":
        secret = app.config.get("SECRET_KEY", "")
        if not isinstance(secret, str) or len(secret) < 32 or secret in {
            "dev-only-change-this-key", "substitua-por-uma-chave-aleatoria-gerada-localmente"
        }:
            raise RuntimeError("Defina uma SECRET_KEY aleatória com pelo menos 32 caracteres em produção.")
        if not app.config.get("TRUSTED_HOSTS"):
            raise RuntimeError("Defina TRUSTED_HOSTS com os domínios autorizados em produção.")
        app.config.update(SESSION_COOKIE_SECURE=True, REMEMBER_COOKIE_SECURE=True)
    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    with app.app_context():
        if db.engine.dialect.name == "sqlite":
            @event.listens_for(db.engine, "connect")
            def sqlite_options(connection, _):
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA busy_timeout=5000")

    from .auth import auth_bp
    from .main import main_bp
    from .models import User
    from .users import users_bp
    from .validation import decimal_br, money, valid_email
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(main_bp)
    app.jinja_env.filters.update(money=money, decimal_br=decimal_br)

    @login_manager.user_loader
    def load_user(identity):
        try:
            user_id, version = (int(part) for part in identity.split(":"))
        except (AttributeError, ValueError):
            return None
        user = db.session.get(User, user_id)
        return user if user and user.active and user.auth_version == version else None

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' https://api.mapbox.com; "
            "style-src 'self' 'unsafe-inline' https://api.mapbox.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https://*.mapbox.com; "
            "connect-src 'self' https://api.mapbox.com https://*.tiles.mapbox.com https://events.mapbox.com; "
            "worker-src 'self' blob:; child-src blob:; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; form-action 'self'"
        )
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        if app.config["APP_ENV"] == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.errorhandler(CSRFError)
    def csrf_error(_):
        return render_template("error.html", code=400, message="O formulário expirou. Atualize a página e envie novamente."), 400

    def error_page(error):
        # A rejected Host has no URL adapter: do not render url_for() templates.
        if isinstance(error, SecurityError):
            return app.response_class("Requisição inválida.", status=400, mimetype="text/plain")
        db.session.rollback()
        messages = {400: "Confira os dados informados.", 403: "Seu perfil não permite esta ação.",
                    404: "A página ou cadastro não foi encontrado.", 413: "O arquivo enviado ultrapassou o limite permitido.",
                    429: "Muitas tentativas. Aguarde 15 minutos e tente novamente.",
                    500: "Não foi possível concluir a operação. Tente novamente."}
        code = error.code or 500
        return render_template("error.html", code=code, message=messages[code]), code
    for code in (400, 403, 404, 413, 429, 500):
        app.register_error_handler(code, error_page)

    @app.cli.command("init-db")
    def init_db_command():
        """Cria tabelas e aplica migrações aditivas sem apagar cadastros."""
        from .migrations import migrate
        migrate()
        click.echo("Banco de dados inicializado. Migrações 1 e 2 aplicadas.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt="Nome")
    @click.option("--email", prompt="E-mail")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin_command(name, email, password):
        """Cria um administrador; não oferece credenciais padrão."""
        email = email.strip().lower()
        if not 2 <= len(name.strip()) <= 120 or not valid_email(email) or not 8 <= len(password) <= 128:
            raise click.ClickException("Confira nome, e-mail e senha (8 a 128 caracteres).")
        if User.query.filter_by(email=email).first():
            raise click.ClickException("Já existe um usuário com esse e-mail.")
        user = User(name=name.strip(), email=email, role="admin", active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Administrador criado com sucesso.")

    @app.cli.command("seed-demo")
    def seed_demo_command():
        """Insere exemplos identificados, apenas em uma base operacional vazia."""
        from .demo import seed_demo
        if app.config["APP_ENV"] == "production":
            raise click.ClickException("Demonstrações são permitidas somente em desenvolvimento.")
        try:
            seed_demo()
        except ValueError as error:
            raise click.ClickException(str(error)) from error
        click.echo("Dados demonstrativos inseridos. Nenhuma API foi conectada.")

    @app.cli.command("backup-db")
    @click.option("--output", type=click.Path(path_type=Path), required=True)
    def backup_db(output):
        """Produz um snapshot SQLite consistente em um arquivo novo."""
        if db.engine.dialect.name != "sqlite":
            raise click.ClickException("Este comando de backup atende a bancos SQLite.")
        if output.exists():
            raise click.ClickException("Escolha um arquivo novo; backups existentes não são sobrescritos.")
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        try:
            with db.engine.connect() as connection, sqlite3.connect(output) as destination:
                connection.connection.driver_connection.backup(destination)
        except Exception:
            output.unlink(missing_ok=True)
            raise
        click.echo(f"Backup criado em {output}.")

    return app
