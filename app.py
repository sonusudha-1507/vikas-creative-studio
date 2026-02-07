from flask import Flask, render_template, request
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
from flask import redirect, url_for, session

app.secret_key = "vikas-secret-key"  # change later
ADMIN_USERNAME = "vikas"
ADMIN_PASSWORD = "vikas123"

# ------------------------
# File upload config
# ------------------------
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "mov", "zip", "pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB


def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------------
# Database helpers
# ------------------------
DB_PATH = "database/projects.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            project_type TEXT NOT NULL,
            description TEXT NOT NULL,
            filename TEXT,
            status TEXT DEFAULT 'Submitted',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ------------------------
# Routes
# ------------------------
@app.route("/")
def home():
    return render_template("home.html", year=datetime.now().year)


@app.route("/start-project", methods=["GET", "POST"])
def start_project():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        project_type = request.form.get("project_type")
        description = request.form.get("description")

        uploaded_file = request.files.get("project_file")
        filename = None

        if uploaded_file and allowed_file(uploaded_file.filename):
            filename = secure_filename(uploaded_file.filename)
            uploaded_file.save(
                os.path.join(app.config["UPLOAD_FOLDER"], filename)
            )

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO projects
            (name, email, project_type, description, filename, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                project_type,
                description,
                filename,
                datetime.now().isoformat()
            )
        )
        conn.commit()
        conn.close()

        return render_template(
            "start_project.html",
            year=datetime.now().year,
            success=True
        )

    return render_template("start_project.html", year=datetime.now().year)
@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    projects = conn.execute(
        "SELECT * FROM projects ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    return render_template(
        "admin.html",
        projects=projects,
        year=datetime.now().year
    )
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))

        return render_template("admin_login.html", error=True)

    return render_template("admin_login.html")
@app.route("/update-status/<int:project_id>", methods=["POST"])
def update_status(project_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    new_status = request.form.get("status")

    conn = get_db_connection()
    conn.execute(
        "UPDATE projects SET status = ? WHERE id = ?",
        (new_status, project_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ------------------------
# App start
# ------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

