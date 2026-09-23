import os

import click
from flask import Flask
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from .config import Config
from .extensions import csrf, db, login_manager


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .auth import auth_bp
    from .main import main_bp
    from .models import User
    from .users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(main_bp)

    def ensure_user_profile_columns():
        """Adiciona os campos de perfil em bancos criados antes do módulo de usuários."""
        inspector = inspect(db.engine)
        if "users" not in inspector.get_table_names():
            return

        existing_columns = {column["name"] for column in inspector.get_columns("users")}
        profile_columns = {
            "phone": "VARCHAR(20)",
            "address": "VARCHAR(255)",
            "cpf": "VARCHAR(11)",
            "birth_date": "DATE",
        }
        for column_name, column_type in profile_columns.items():
            if column_name not in existing_columns:
                db.session.execute(
                    text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                )
        db.session.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_cpf ON users (cpf)")
        )
        db.session.commit()

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.cli.command("init-db")
    def init_db_command():
        """Cria as tabelas do banco de dados."""
        db.create_all()
        ensure_user_profile_columns()
        click.echo("Banco de dados inicializado.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt="Nome")
    @click.option("--email", prompt="E-mail")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin_command(name, email, password):
        """Cria o primeiro usuário administrador."""
        normalized_email = email.strip().lower()
        if User.query.filter_by(email=normalized_email).first():
            raise click.ClickException("Já existe um usuário com esse e-mail.")

        user = User(
            name=name.strip(),
            email=normalized_email,
            password_hash=generate_password_hash(password),
            role="admin",
            active=True,
        )
        db.session.add(user)
        db.session.commit()
        click.echo("Administrador criado com sucesso.")

    return app
