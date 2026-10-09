"""In-browser previews. Native types (PDF, images, media, text) are shown by the
browser itself; Word/PowerPoint/Excel files are rendered client-side by the
JavaScript libraries in static/vendor, so nothing needs installing on the server
and files never leave it."""

import os

from flask import abort, render_template, send_from_directory
from werkzeug.utils import secure_filename

from storage_utils import user_dir

KINDS = {
    "pdf": {"pdf"},
    "image": {"png", "jpg", "jpeg", "gif", "webp", "bmp"},
    "video": {"mp4", "webm", "ogv", "mov"},
    "audio": {"mp3", "wav", "ogg", "m4a", "flac"},
    "text": {"txt", "md", "log", "json", "xml"},
    "docx": {"docx"},
    "pptx": {"pptx"},
    "sheet": {"xlsx", "xlsm", "xls", "ods", "csv"},
}
_BY_EXT = {ext: kind for kind, exts in KINDS.items() for ext in exts}
# Rendered by JavaScript in the viewer page rather than by the browser.
CLIENT_RENDERED = {"docx", "pptx", "sheet"}

# Viewer pages only run our own scripts; office renderers need inline styles
# and blob:/data: images.
VIEWER_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' blob: data:; font-src 'self' data:; media-src 'self'; "
    "object-src 'none'; frame-src 'self'; base-uri 'none'; form-action 'self'"
)


def preview_kind(filename):
    return _BY_EXT.get(filename.rsplit(".", 1)[-1].lower()) if "." in filename else None


def _file_or_404(user_id, filename):
    name = secure_filename(filename)
    if not name or not os.path.isfile(os.path.join(user_dir(user_id), name)):
        abort(404)
    return name


def render_viewer(user_id, filename, raw_url, download_url, back_url):
    name = _file_or_404(user_id, filename)
    kind = preview_kind(name)
    html = render_template(
        "viewer.html", name=name, kind=kind, client_rendered=kind in CLIENT_RENDERED,
        raw_url=raw_url, download_url=download_url, back_url=back_url,
    )
    return html, 200, {"Content-Security-Policy": VIEWER_CSP}


def serve_raw(user_id, filename):
    name = _file_or_404(user_id, filename)
    kind = preview_kind(name)
    if kind is None:
        abort(404)
    if kind == "text":
        resp = send_from_directory(user_dir(user_id), name, mimetype="text/plain; charset=utf-8")
    elif kind in CLIENT_RENDERED:
        # Fetched as bytes by the viewer's JavaScript, never rendered directly.
        resp = send_from_directory(user_dir(user_id), name, mimetype="application/octet-stream")
    else:
        resp = send_from_directory(user_dir(user_id), name)
    resp.headers["Content-Disposition"] = "inline"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Cache-Control"] = "private, no-store"
    return resp
