from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from .extensions import db
from .models import User


users_bp = Blueprint("users", __name__)


def _require_admin():
    if current_user.role != "admin":
        abort(403)


def _normalize_cpf(value):
    return "".join(character for character in value if character.isdigit())


def _user_form_data():
    birth_date_value = request.form.get("birth_date", "").strip()
    try:
        birth_date = datetime.strptime(birth_date_value, "%Y-%m-%d").date()
    except ValueError:
        birth_date = None
    return {
        "name": request.form.get("name", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "address": request.form.get("address", "").strip(),
        "cpf": _normalize_cpf(request.form.get("cpf", "")),
        "birth_date": birth_date,
        "role": request.form.get("role", "").strip().lower(),
        "active": request.form.get("active") == "on",
    }


def _validate_user_data(data, user_id=None):
    required_values = (
        data["name"], data["phone"], data["email"], data["address"],
        data["cpf"], data["birth_date"], data["role"],
    )
    if not all(required_values):
        return "Preencha todos os campos obrigatórios."
    if len(data["cpf"]) != 11:
        return "Informe um CPF com 11 dígitos."
    if data["role"] not in {"admin", "supervisor"}:
        return "Selecione uma função válida."
    if User.query.filter(User.email == data["email"], User.id != user_id).first():
        return "Já existe um usuário com esse e-mail."
    if User.query.filter(User.cpf == data["cpf"], User.id != user_id).first():
        return "Já existe um usuário com esse CPF."
    return None


@users_bp.get("/usuarios")
@login_required
def users():
    _require_admin()
    search = request.args.get("busca", "").strip()
    query = User.query
    if search:
        like_term = f"%{search}%"
        cpf_search = _normalize_cpf(search)
        filters = [User.name.ilike(like_term), User.email.ilike(like_term)]
        if cpf_search:
            filters.append(User.cpf.ilike(f"%{cpf_search}%"))
        query = query.filter(or_(*filters))
    all_users = query.order_by(User.name.asc()).all()
    totals = {
        "all": User.query.count(),
        "active": User.query.filter_by(active=True).count(),
        "admins": User.query.filter_by(role="admin").count(),
        "supervisors": User.query.filter_by(role="supervisor").count(),
    }
    return render_template("users.html", users=all_users, totals=totals, search=search)


@users_bp.post("/usuarios/novo")
@login_required
def create_user():
    _require_admin()
    data = _user_form_data()
    error = _validate_user_data(data)
    password = request.form.get("password", "")
    if not password or len(password) < 8:
        error = error or "A senha deve possuir pelo menos 8 caracteres."
    if error:
        flash(error, "error")
        return redirect(url_for("users.users"))
    user = User(**data)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("Usuário cadastrado com sucesso.", "success")
    return redirect(url_for("users.users"))


@users_bp.post("/usuarios/<int:user_id>/editar")
@login_required
def edit_user(user_id):
    _require_admin()
    user = db.get_or_404(User, user_id)
    data = _user_form_data()
    error = _validate_user_data(data, user_id=user.id)
    password = request.form.get("password", "")
    if password and len(password) < 8:
        error = error or "A nova senha deve possuir pelo menos 8 caracteres."
    if user.id == current_user.id and not data["active"]:
        error = error or "Você não pode desativar o próprio usuário."
    if error:
        flash(error, "error")
        return redirect(url_for("users.users"))
    for field, value in data.items():
        setattr(user, field, value)
    if password:
        user.set_password(password)
    db.session.commit()
    flash("Usuário atualizado com sucesso.", "success")
    return redirect(url_for("users.users"))
