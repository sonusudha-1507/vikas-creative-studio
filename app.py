from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_from_directory
)

from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import sqlite3
import razorpay
import os

from routes.auth import auth_bp
from routes.client import client_bp
from routes.admin import admin_bp
from routes.chat import chat_bp
from routes.services import services_bp
from routes.payment import payment_bp
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from flask import jsonify
from models.database import init_database

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "vikas-secret-key"
)

# -----------------------------
# Register Blueprints
# -----------------------------

app.register_blueprint(auth_bp)
app.register_blueprint(client_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(services_bp)
app.register_blueprint(payment_bp)

# -----------------------------
# Config
# -----------------------------

UPLOAD_FOLDER = "uploads"
DELIVERY_FOLDER = "deliveries"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DELIVERY_FOLDER"] = DELIVERY_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

DB_PATH = "database/projects.db"

razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)

# -----------------------------
# Helpers
# -----------------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,
        email TEXT,

        project_type TEXT,
        description TEXT,

        filename TEXT,

        service_name TEXT,
        package_name TEXT,

        price INTEGER,

        payment_status TEXT DEFAULT 'Pending',
        payment_id TEXT,

        user_id INTEGER,

        delivery_file TEXT,

        status TEXT DEFAULT 'Submitted',

        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        sender TEXT,
        message TEXT,
        created_at TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        project_id INTEGER,
        user_id INTEGER,

        razorpay_payment_id TEXT,

        amount INTEGER,

        status TEXT,

        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# Delivery
# -----------------------------

@app.route("/deliver/<int:project_id>", methods=["POST"])
def deliver_project(project_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    file = request.files.get("delivery")

    if not file or file.filename == "":
        return redirect("/admin")

    filename = secure_filename(file.filename)

    os.makedirs(
        app.config["DELIVERY_FOLDER"],
        exist_ok=True
    )

    file.save(
        os.path.join(
            app.config["DELIVERY_FOLDER"],
            filename
        )
    )

    conn = get_db_connection()

    project = conn.execute(
        """
        SELECT *

        FROM projects

        WHERE id=?
        """,
        (
            project_id,
        )
    ).fetchone()

    if project is None:

        conn.close()

        return redirect("/admin")

    conn.execute(
        """
        UPDATE projects

        SET

            delivery_file=?,
            status='Delivered'

        WHERE id=?
        """,
        (
            filename,
            project_id
        )
    )

    conn.execute(
        """
        INSERT INTO notifications(

            user_id,

            project_id,

            title,

            description,

            created_at

        )

        VALUES(

            ?,?,?,?,?

        )
        """,
        (
            project["user_id"],
            project_id,
            "Project Delivered",
            "Your project has been completed. You can now download the final files from your dashboard.",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()

    conn.close()

    return redirect("/admin")

@app.route("/download/<filename>")
def download(filename):

    return send_from_directory(
        app.config["DELIVERY_FOLDER"],
        filename,
        as_attachment=True
    )


# -----------------------------
# Payment Blueprint bridge
# -----------------------------

@app.context_processor
def inject_keys():

    return {

        "RAZORPAY_KEY_ID":
        os.getenv("RAZORPAY_KEY_ID")

    }

# -----------------------------
# Start
# -----------------------------

if __name__ == "__main__":

    os.makedirs("uploads", exist_ok=True)
    os.makedirs("deliveries", exist_ok=True)
    os.makedirs("database", exist_ok=True)

    init_database()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))