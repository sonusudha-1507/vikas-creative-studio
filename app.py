from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
app.secret_key = "vikas-secret-key"

ADMIN_USERNAME = "vikas"
ADMIN_PASSWORD = "vikas123"

# ------------------------
# File upload config
# ------------------------
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "mov", "zip", "pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------------
# Database
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
            name TEXT,
            email TEXT,
            project_type TEXT,
            description TEXT,
            filename TEXT,
            service_name TEXT,
            package_name TEXT,
            price INTEGER,
            status TEXT DEFAULT 'Submitted',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


# ------------------------
# ROUTES
# ------------------------

@app.route("/")
def home():
    return render_template("home.html", year=datetime.now().year)


# ------------------------
# SERVICES
# ------------------------
@app.route("/services")
def services():
    return render_template("services.html", year=datetime.now().year)


@app.route("/services/photo-editing")
def photo_editing():
    return render_template("service_photo.html", year=datetime.now().year)


# ------------------------
# START PROJECT (MAIN ORDER FLOW)
# ------------------------
@app.route("/start-project", methods=["GET", "POST"])
def start_project():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        project_type = request.form.get("project_type")
        description = request.form.get("description")

        service_name = request.form.get("service")
        package_name = request.form.get("package")
        price = request.form.get("price")

        file = request.files.get("project_file")
        filename = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO projects
            (name, email, project_type, description, filename,
             service_name, package_name, price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                project_type,
                description,
                filename,
                service_name,
                package_name,
                price,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        conn.commit()
        conn.close()

        return redirect(url_for("thank_you"))

    # GET request
    service = request.args.get("service")
    package = request.args.get("package")
    price = request.args.get("price")

    return render_template(
        "start_project.html",
        service=service,
        package=package,
        price=price,
        year=datetime.now().year
    )


@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html", year=datetime.now().year)


# ------------------------
# ADMIN
# ------------------------
@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    projects = conn.execute(
        "SELECT * FROM projects ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    return render_template("admin.html", projects=projects, year=datetime.now().year)


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
# TRACK PROJECT
# ------------------------
@app.route("/track-project", methods=["GET", "POST"])
def track_project():
    projects = None

    if request.method == "POST":
        email = request.form.get("email")

        conn = get_db_connection()
        projects = conn.execute(
            "SELECT * FROM projects WHERE email = ? ORDER BY created_at DESC",
            (email,)
        ).fetchall()
        conn.close()

    return render_template("track_project.html", projects=projects, year=datetime.now().year)


# ------------------------
# START APP
# ------------------------
if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("database", exist_ok=True)
    init_db()
    app.run(debug=True)
