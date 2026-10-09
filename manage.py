"""Command-line helpers.

    python manage.py create-admin <username>
"""

import getpass
import sqlite3
import sys

from werkzeug.security import generate_password_hash

from app import app
from storage_utils import user_dir


def create_admin(username):
    password = getpass.getpass("Password: ")
    if len(password) < 8:
        sys.exit("Password must be at least 8 characters.")
    if password != getpass.getpass("Repeat password: "):
        sys.exit("Passwords do not match.")
    with app.app_context():
        conn = sqlite3.connect(app.config["DATABASE"])
        try:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                (username, generate_password_hash(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            sys.exit(f"User '{username}' already exists.")
        finally:
            conn.close()
        user_dir(cur.lastrowid, create=True)
    print(f"Admin '{username}' created.")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "create-admin":
        create_admin(sys.argv[2])
    else:
        sys.exit(__doc__)
