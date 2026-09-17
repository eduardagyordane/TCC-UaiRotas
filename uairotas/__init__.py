import os

import click
from flask import Flask
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.cli.command("init-db")
    def init_db_command():
        """Cria as tabelas do banco de dados."""
        db.create_all()
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

