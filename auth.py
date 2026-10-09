import time
from collections import defaultdict
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from werkzeug.security import check_password_hash

from db import get_db

bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = None

# Simple in-memory brute-force protection: max attempts per IP per window.
MAX_ATTEMPTS = 10
WINDOW_SECONDS = 15 * 60
_failed = defaultdict(list)


class User(UserMixin):
    def __init__(self, row):
        self.id = row["id"]
        self.username = row["username"]
        self.is_admin = bool(row["is_admin"])


@login_manager.user_loader
def load_user(user_id):
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(row) if row else None


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _too_many_attempts(ip):
    now = time.time()
    _failed[ip] = [t for t in _failed[ip] if now - t < WINDOW_SECONDS]
    return len(_failed[ip]) >= MAX_ATTEMPTS


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        if _too_many_attempts(ip):
            flash("Too many failed attempts. Try again in a few minutes.", "error")
            return render_template("login.html"), 429

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if row and check_password_hash(row["password_hash"], password):
            _failed.pop(ip, None)
            login_user(User(row))
            return redirect(url_for("index"))

        _failed[ip].append(time.time())
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
