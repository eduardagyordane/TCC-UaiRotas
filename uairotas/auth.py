from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from werkzeug.security import check_password_hash, generate_password_hash
from .models import LoginAttempt, User
from .extensions import db


auth_bp = Blueprint("auth", __name__)
_DUMMY_HASH = generate_password_hash("not-a-login-credential")


def is_safe_redirect(target):
    if len(target) > 2048 or "\\" in target or any(ord(c) < 32 for c in target):
        return False
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in {"http", "https"} and host_url.netloc == redirect_url.netloc


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        now = datetime.now(timezone.utc)
        since = now - timedelta(seconds=current_app.config["LOGIN_WINDOW_SECONDS"])
        LoginAttempt.query.filter(LoginAttempt.created_at < since).delete()
        def bucket(value):
            return hmac.new(current_app.secret_key.encode(), value.encode(), hashlib.sha256).hexdigest()
        # Do not trust a client-provided X-Forwarded-For header.
        account_bucket = bucket("account:" + email[:255])
        ip_bucket = bucket("ip:" + (request.remote_addr or "unknown"))
        account_count = LoginAttempt.query.filter_by(bucket=account_bucket).count()
        ip_count = LoginAttempt.query.filter_by(bucket=ip_bucket).count()
        if account_count >= current_app.config["LOGIN_ATTEMPT_LIMIT"] or ip_count >= current_app.config["LOGIN_IP_LIMIT"]:
            db.session.commit()
            response = current_app.make_response((render_template("auth/login.html", email=email[:255], throttled=True), 429))
            response.headers["Retry-After"] = str(current_app.config["LOGIN_WINDOW_SECONDS"])
            return response
        user = User.query.filter_by(email=email).first() if len(email) <= 255 else None
        password_ok = check_password_hash(user.password_hash if user else _DUMMY_HASH, password) if len(password) <= 128 else False

        if user and user.is_active and password_ok:
            LoginAttempt.query.filter_by(bucket=account_bucket).delete()
            db.session.commit()
            session.clear()
            session.permanent = True
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            if next_page and is_safe_redirect(next_page):
                return redirect(next_page)
            return redirect(url_for("main.home"))

        db.session.add_all([LoginAttempt(bucket=account_bucket), LoginAttempt(bucket=ip_bucket)])
        db.session.commit()
        flash("E-mail ou senha inválidos.", "error")

    return render_template("auth/login.html", email=request.form.get("email", "")[:255])


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada com segurança.", "success")
    return redirect(url_for("auth.login"))
