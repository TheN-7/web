import os
import shutil
from datetime import datetime

from flask import current_app


def user_dir(user_id, create=False):
    """Absolute path of a user's private folder, keyed by numeric id."""
    path = os.path.join(current_app.config["STORAGE_DIR"], str(int(user_id)))
    if create:
        os.makedirs(path, exist_ok=True)
    return path


def list_files(user_id):
    path = user_dir(user_id)
    if not os.path.isdir(path):
        return []
    files = []
    for entry in os.scandir(path):
        if entry.is_file():
            st = entry.stat()
            files.append(
                {
                    "name": entry.name,
                    "size": st.st_size,
                    "modified": datetime.fromtimestamp(st.st_mtime),
                }
            )
    return sorted(files, key=lambda f: f["name"].lower())


def remove_user_dir(user_id):
    shutil.rmtree(user_dir(user_id), ignore_errors=True)


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
