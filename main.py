"""Production entry point (e.g. SparkedHost / Pterodactyl "App py file").

Serves the app with waitress on 0.0.0.0:<SERVER_PORT or PORT>. On first start,
if no users exist, an `admin` account is created and its password printed to
the console once - log in and change it from the admin page.
"""

import os
import secrets
import sqlite3

from waitress import serve
from werkzeug.security import generate_password_hash

from app import app
from storage_utils import user_dir


def bootstrap_admin():
    with app.app_context():
        conn = sqlite3.connect(app.config["DATABASE"])
        try:
            if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
                return
            password = secrets.token_urlsafe(12)
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES ('admin', ?, 1)",
                (generate_password_hash(password),),
            )
            conn.commit()
            user_dir(cur.lastrowid, create=True)
        finally:
            conn.close()
    print("=" * 60)
    print("First start: created admin account")
    print("  username: admin")
    print(f"  password: {password}")
    print("Log in and change it under Users > admin > Reset password.")
    print("=" * 60, flush=True)


if __name__ == "__main__":
    bootstrap_admin()
    port = int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or 8000)
    print(f"File Portal listening on 0.0.0.0:{port}", flush=True)
    serve(app, host="0.0.0.0", port=port, threads=8, max_request_body_size=app.config["MAX_CONTENT_LENGTH"])
