import os
import sqlite3

from flask import Blueprint, abort, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from auth import admin_required
from db import get_db
from preview import render_viewer, serve_raw
from storage_utils import list_files, remove_user_dir, user_dir

bp = Blueprint("admin", __name__, url_prefix="/admin")

MIN_PASSWORD = 8


def _get_user_or_404(user_id):
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        abort(404)
    return row


@bp.route("/")
@admin_required
def users():
    rows = get_db().execute("SELECT * FROM users ORDER BY is_admin DESC, username").fetchall()
    users = []
    for row in rows:
        files = list_files(row["id"])
        users.append({**dict(row), "file_count": len(files), "total_size": sum(f["size"] for f in files)})
    stats = {
        "users": len(users),
        "admins": sum(1 for u in users if u["is_admin"]),
        "files": sum(u["file_count"] for u in users),
        "size": sum(u["total_size"] for u in users),
    }
    return render_template("admin/users.html", users=users, stats=stats)


@bp.route("/users", methods=["POST"])
@admin_required
def add_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    is_admin = 1 if request.form.get("is_admin") else 0

    if not username or len(username) > 64:
        flash("Username is required (max 64 characters).", "error")
    elif len(password) < MIN_PASSWORD:
        flash(f"Password must be at least {MIN_PASSWORD} characters.", "error")
    else:
        db = get_db()
        try:
            cur = db.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), is_admin),
            )
            db.commit()
            user_dir(cur.lastrowid, create=True)
            flash(f"User '{username}' created.", "success")
        except sqlite3.IntegrityError:
            flash(f"Username '{username}' already exists.", "error")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    row = _get_user_or_404(user_id)
    if row["id"] == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("admin.users"))
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    remove_user_dir(user_id)
    flash(f"User '{row['username']}' and all their files were deleted.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:user_id>/password", methods=["POST"])
@admin_required
def reset_password(user_id):
    row = _get_user_or_404(user_id)
    password = request.form.get("password", "")
    if len(password) < MIN_PASSWORD:
        flash(f"Password must be at least {MIN_PASSWORD} characters.", "error")
    else:
        db = get_db()
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (generate_password_hash(password), user_id),
        )
        db.commit()
        flash(f"Password for '{row['username']}' updated.", "success")
    return redirect(request.referrer or url_for("admin.users"))


@bp.route("/users/<int:user_id>/files")
@admin_required
def user_files(user_id):
    row = _get_user_or_404(user_id)
    return render_template("admin/user_files.html", user=row, files=list_files(user_id))


@bp.route("/users/<int:user_id>/files", methods=["POST"])
@admin_required
def upload(user_id):
    _get_user_or_404(user_id)
    folder = user_dir(user_id, create=True)
    saved = 0
    for f in request.files.getlist("files"):
        name = secure_filename(f.filename or "")
        if not name:
            continue
        f.save(os.path.join(folder, name))
        saved += 1
    flash(f"Uploaded {saved} file(s)." if saved else "No files selected.", "success" if saved else "error")
    return redirect(url_for("admin.user_files", user_id=user_id))


@bp.route("/users/<int:user_id>/files/<path:filename>/download")
@admin_required
def download(user_id, filename):
    _get_user_or_404(user_id)
    return send_from_directory(user_dir(user_id), secure_filename(filename), as_attachment=True)


@bp.route("/users/<int:user_id>/files/<path:filename>/view")
@admin_required
def view(user_id, filename):
    _get_user_or_404(user_id)
    return render_viewer(
        user_id, filename,
        raw_url=url_for("admin.raw", user_id=user_id, filename=filename),
        download_url=url_for("admin.download", user_id=user_id, filename=filename),
        back_url=url_for("admin.user_files", user_id=user_id),
    )


@bp.route("/users/<int:user_id>/files/<path:filename>/raw")
@admin_required
def raw(user_id, filename):
    _get_user_or_404(user_id)
    return serve_raw(user_id, filename)


@bp.route("/users/<int:user_id>/files/<path:filename>/delete", methods=["POST"])
@admin_required
def delete_file(user_id, filename):
    _get_user_or_404(user_id)
    path = os.path.join(user_dir(user_id), secure_filename(filename))
    if os.path.isfile(path):
        os.remove(path)
        flash(f"Deleted '{os.path.basename(path)}'.", "success")
    else:
        flash("File not found.", "error")
    return redirect(url_for("admin.user_files", user_id=user_id))
