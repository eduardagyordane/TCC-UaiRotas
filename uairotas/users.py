from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import AuditLog, User
from .validation import Form, digits, today, valid_cpf, valid_email, valid_phone

users_bp = Blueprint("users", __name__)


def require_admin():
    if current_user.role != "admin":
        abort(403)


def user_data(values, user_id=None, profile=False):
    form = Form(values)
    data = {"name": form.text("name", "nome", 120), "phone": digits(form.text("phone", "telefone", 20, not profile)),
            "email": form.text("email", "e-mail", 255).lower(), "address": form.text("address", "endereço", 255, not profile),
            "cpf": digits(form.text("cpf", "CPF", 14, not profile)) or None,
            "birth_date": form.date("birth_date", "Nascimento", not profile, past=True)}
    if not profile:
        data.update(role=form.choice("role", "Função", ("admin", "supervisor")), active=values.get("active") == "on")
    if not valid_email(data["email"]):
        form.errors["email"] = "Informe um e-mail válido."
    if (not profile or values.get("phone", "").strip()) and not valid_phone(data["phone"]):
        form.errors["phone"] = "Informe um telefone com DDD e 10 ou 11 dígitos."
    if (not profile or values.get("cpf", "").strip()) and not valid_cpf(data["cpf"] or ""):
        form.errors["cpf"] = "Informe um CPF válido, com dígitos verificadores corretos."
    if User.query.filter(User.email == data["email"], User.id != user_id).first():
        form.errors["email"] = "Já existe um usuário com esse e-mail."
    if data["cpf"] and User.query.filter(User.cpf == data["cpf"], User.id != user_id).first():
        form.errors["cpf"] = "Já existe um usuário com esse CPF."
    return data, form.errors


def page_number():
    raw = request.args.get("pagina", "1")
    if not raw.isascii() or not raw.isdigit() or not 1 <= int(raw[:7]) <= 1_000_000 or len(raw) > 7:
        abort(400)
    return int(raw)


def render_users(values=None, errors=None, editing_id=None, status=200):
    search = request.args.get("busca", "").strip()[:120]
    query = User.query
    if search:
        term = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        filters = [User.name.ilike(f"%{term}%", escape="\\"), User.email.ilike(f"%{term}%", escape="\\")]
        cpf = digits(search)
        if cpf:
            filters.append(User.cpf.like(f"%{cpf}%"))
        query = query.filter(or_(*filters))
    pagination = query.order_by(User.name, User.id).paginate(page=page_number(), per_page=25, error_out=False)
    totals = {"all": User.query.count(), "active": User.query.filter_by(active=True).count(),
              "admins": User.query.filter_by(role="admin", active=True).count(),
              "supervisors": User.query.filter_by(role="supervisor", active=True).count()}
    return render_template("users.html", users=pagination.items, pagination=pagination, totals=totals, search=search,
                           form_values=values or {}, errors=errors or {}, editing_id=editing_id, today=today()), status


@users_bp.get("/usuarios")
@login_required
def users():
    require_admin()
    return render_users()


@users_bp.get("/usuarios/<int:user_id>/dados")
@login_required
def user_details(user_id):
    require_admin()
    user = db.get_or_404(User, user_id)
    return jsonify({"name": user.name, "phone": user.phone or "", "email": user.email, "address": user.address or "",
                    "cpf": user.cpf or "", "birth_date": user.birth_date.isoformat() if user.birth_date else "",
                    "role": user.role, "active": user.active, "action": url_for("users.edit_user", user_id=user.id)})


def save_user(user=None):
    require_admin()
    data, errors = user_data(request.form, user.id if user else None)
    password = request.form.get("password", "")
    if (not user or password) and not 8 <= len(password) <= 128:
        errors["password"] = "A senha deve possuir de 8 a 128 caracteres."
    if user and user.id == current_user.id and not data["active"]:
        errors["active"] = "Você não pode desativar o próprio usuário."
    if user and user.role == "admin" and user.active and (data["role"] != "admin" or not data["active"]):
        if User.query.filter_by(role="admin", active=True).count() <= 1:
            errors["role"] = "Mantenha pelo menos um administrador ativo."
    safe_values = {key: value for key, value in request.form.items() if key not in ("password", "csrf_token")}
    if errors:
        return render_users(safe_values, errors, user.id if user else None, 422)
    is_new = user is None
    if is_new:
        user = User(**data)
        db.session.add(user)
    else:
        if password or data["role"] != user.role or data["active"] != user.active or data["email"] != user.email:
            user.auth_version += 1
        for key, value in data.items():
            setattr(user, key, value)
    if password:
        user.set_password(password)
    actor_id = current_user.id
    try:
        db.session.flush()
        db.session.add(AuditLog(actor_id=actor_id, action="create" if is_new else "update", entity="user", entity_id=user.id))
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        message = "Mantenha pelo menos um administrador ativo." if "last_active_admin" in str(error.orig) else "E-mail ou CPF já cadastrado. Confira os dados."
        return render_users(safe_values, {"_form": message}, user.id if not is_new else None, 409)
    if user.id == actor_id:
        login_user(user, fresh=True)
    flash("Usuário cadastrado com sucesso." if is_new else "Usuário atualizado com sucesso.", "success")
    if current_user.role == "admin":
        return redirect(url_for("users.users", busca=request.args.get("busca", "")[:120], pagina=page_number()))
    return redirect(url_for("main.home"))


@users_bp.post("/usuarios/novo")
@login_required
def create_user():
    return save_user()


@users_bp.post("/usuarios/<int:user_id>/editar")
@login_required
def edit_user(user_id):
    require_admin()
    return save_user(db.get_or_404(User, user_id))


@users_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user._get_current_object()
    errors = {}
    if request.method == "POST":
        data, errors = user_data(request.form, user.id, profile=True)
        password = request.form.get("password", "")
        if password or data["email"] != user.email:
            old_password = request.form.get("current_password", "")
            if len(old_password) > 128 or not user.check_password(old_password):
                errors["current_password"] = "Confirme sua senha atual para alterar e-mail ou senha."
        if password and not 8 <= len(password) <= 128:
            errors["password"] = "A senha deve possuir de 8 a 128 caracteres."
        if password != request.form.get("password_confirmation", ""):
            errors["password_confirmation"] = "As senhas não coincidem."
        if not errors:
            if password or data["email"] != user.email:
                user.auth_version += 1
            for key, value in data.items():
                setattr(user, key, value)
            if password:
                user.set_password(password)
            db.session.add(AuditLog(actor_id=user.id, action="update_profile", entity="user", entity_id=user.id))
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                errors["_form"] = "E-mail ou CPF já cadastrado."
            else:
                login_user(user, fresh=True)
                flash("Perfil atualizado com sucesso.", "success")
                return redirect(url_for("users.profile"))
    values = dict(request.form) if request.method == "POST" else {key: getattr(user, key) or "" for key in ("name", "phone", "email", "address", "cpf", "birth_date")}
    for key in ("password", "current_password", "password_confirmation", "csrf_token"):
        values.pop(key, None)
    return render_template("profile.html", form_values=values, errors=errors, today=today()), 422 if errors else 200
