import os
import secrets

from flask import Flask, redirect, render_template, send_from_directory, url_for
from flask_login import current_user, login_required
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename

import admin
import auth
from db import init_db
from icons import icon
from preview import preview_kind, render_viewer, serve_raw
from storage_utils import human_size, list_files, user_dir

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_DIR = os.path.join(BASE_DIR, "static", "custom")
CUSTOM_IMAGES = {
    "background": ("jpg", "jpeg", "png", "webp", "gif"),
    "logo": ("png", "svg", "webp", "jpg", "jpeg"),
    "favicon": ("ico", "png", "svg"),
}


def custom_images():
    """URLs of user-supplied images in static/custom/ (background.*, logo.*)."""
    found = {}
    for name, exts in CUSTOM_IMAGES.items():
        for ext in exts:
            path = os.path.join(CUSTOM_DIR, f"{name}.{ext}")
            if os.path.isfile(path):
                # mtime in the URL so browsers pick up a replaced image right away
                found[name] = url_for("static", filename=f"custom/{name}.{ext}", v=int(os.path.getmtime(path)))
                break
    # No favicon of its own? Use the logo for the browser tab too.
    if "favicon" not in found and "logo" in found:
        found["favicon"] = found["logo"]
    return found


def _secret_key(instance_dir):
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    key_file = os.path.join(instance_dir, "secret_key")
    if not os.path.exists(key_file):
        with open(key_file, "w") as fh:
            fh.write(secrets.token_hex(32))
        os.chmod(key_file, 0o600)
    with open(key_file) as fh:
        return fh.read().strip()


def create_app():
    instance_dir = os.environ.get("INSTANCE_DIR", os.path.join(BASE_DIR, "instance"))
    os.makedirs(instance_dir, exist_ok=True)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=_secret_key(instance_dir),
        DATABASE=os.path.join(instance_dir, "app.db"),
        STORAGE_DIR=os.environ.get("STORAGE_DIR", os.path.join(BASE_DIR, "storage")),
        MAX_CONTENT_LENGTH=int(os.environ.get("MAX_UPLOAD_MB", "200")) * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Set SECURE_COOKIES=1 once the site is served over HTTPS.
        SESSION_COOKIE_SECURE=os.environ.get("SECURE_COOKIES") == "1",
        REMEMBER_COOKIE_SECURE=os.environ.get("SECURE_COOKIES") == "1",
    )
    os.makedirs(app.config["STORAGE_DIR"], exist_ok=True)

    init_db(app)
    CSRFProtect(app)
    auth.login_manager.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.jinja_env.filters["filesize"] = human_size
    app.jinja_env.filters["previewable"] = preview_kind
    app.jinja_env.globals["icon"] = icon

    @app.context_processor
    def inject_custom_images():
        return {"custom": custom_images()}

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        return redirect(url_for("admin.users" if current_user.is_admin else "files"))

    # The folder is always taken from the logged-in session, never from the URL,
    # so a user can only ever reach their own files.
    @app.route("/files")
    @login_required
    def files():
        return render_template("files.html", files=list_files(current_user.id))

    @app.route("/files/<path:filename>/download")
    @login_required
    def download(filename):
        return send_from_directory(user_dir(current_user.id), secure_filename(filename), as_attachment=True)

    @app.route("/files/<path:filename>/view")
    @login_required
    def view(filename):
        return render_viewer(
            current_user.id, filename,
            raw_url=url_for("raw", filename=filename),
            download_url=url_for("download", filename=filename),
            back_url=url_for("files"),
        )

    @app.route("/files/<path:filename>/raw")
    @login_required
    def raw(filename):
        return serve_raw(current_user.id, filename)

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403, message="You don't have access to this page."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="Page or file not found."), 404

    @app.errorhandler(413)
    def too_large(_e):
        mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return render_template("error.html", code=413, message=f"Upload too large (max {mb} MB)."), 413

    return app


app = create_app()
