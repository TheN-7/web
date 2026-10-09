# File Portal

A small Flask site where each user logs in and sees **only their own private folder**.
Admins add/remove users, reset passwords, and upload/delete files in any user's folder.
Regular users can view and download their files.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py create-admin admin   # optional, prompts for a password
```

## In-browser previews

Files can be opened with **View** instead of downloading. Nothing extra needs
installing on the server, and files never leave it:

- PDF, images, video, audio, text: shown by the browser itself.
- Word (`.docx`), PowerPoint (`.pptx`), Excel (`.xlsx .xlsm .xls .ods .csv`):
  rendered in the viewer's browser by the JavaScript libraries in `static/vendor/`
  (docx-preview, pptx-preview, SheetJS). Complex slides (animations, SmartArt,
  unusual fonts) may look slightly different from PowerPoint.
- Old `.doc` / `.ppt` and other types: download only.

## Custom background & logo

Put your own images in `static/custom/` (see `PUT-IMAGES-HERE.txt` there):

- `background.jpg` / `.png` / `.webp` / `.gif`: full-screen background behind the glass
- `logo.png` / `.svg` / `.webp` / `.jpg`: replaces the folder icon (square works best)
- `favicon.ico` / `.png` / `.svg`: browser-tab icon (falls back to the logo if missing)

They're picked up on the next page refresh; no restart needed. On SparkedHost,
upload them to that folder with the File Manager.

## Run (development)

```bash
.venv/bin/flask --app app run --debug
```

Open http://127.0.0.1:5000 and log in with the admin account.

## Deploy on SparkedHost (Python server)

1. Upload the project files (everything except `.venv/`, `instance/`, `storage/`)
   through the panel's File Manager or SFTP.
2. In **Startup**, set the app file to `main.py` (requirements are installed from
   `requirements.txt` automatically).
3. Start the server. On the very first start the console prints a generated
   `admin` password. Log in at `http://<server-ip>:<port>` and change it under
   **Users → admin → Reset password**.

`main.py` listens on the port SparkedHost assigns (`SERVER_PORT`). The SQLite
database lives in `instance/` and the users' files in `storage/` on the server.
Back these up from the File Manager.

If you add a domain with HTTPS in front of it, set `SECURE_COOKIES=1`.

## Run (any other server)

```bash
.venv/bin/python main.py           # waitress on 0.0.0.0:8000 (or $PORT)
```

## Configuration (environment variables)

| Variable         | Default            | Meaning                                  |
|------------------|--------------------|------------------------------------------|
| `SECRET_KEY`     | auto, `instance/`  | Session signing key                      |
| `STORAGE_DIR`    | `./storage`        | Where user folders live                  |
| `MAX_UPLOAD_MB`  | `200`              | Max size of one upload request           |
| `SECURE_COOKIES` | off                | Set to `1` when served over HTTPS        |

## Where things live

- `instance/app.db` — SQLite user database (passwords are hashed)
- `storage/<user id>/` — each user's private folder

Back up both `instance/` and `storage/`.
