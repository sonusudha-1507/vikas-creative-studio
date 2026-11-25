import os
from datetime import datetime
from flask import (
    Flask,
    redirect,
    request,
    session,
    send_from_directory,
    flash,
    abort,
)
from werkzeug.utils import secure_filename

import config
from models.database import get_db_connection, init_database
from routes.auth import auth_bp
from routes.client import client_bp
from routes.admin import admin_bp
from routes.chat import chat_bp
from routes.services import services_bp
from routes.payment import payment_bp

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
app.config["DELIVERY_FOLDER"] = config.DELIVERY_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["DELIVERY_FOLDER"], exist_ok=True)
os.makedirs(os.path.dirname(config.DATABASE) or "database", exist_ok=True)
init_database()

app.register_blueprint(auth_bp)
app.register_blueprint(client_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(services_bp)
app.register_blueprint(payment_bp)


@app.route("/health")
def health():
    return "OK", 200


@app.route("/deliver/<int:project_id>", methods=["POST"])
def deliver_project(project_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    file = request.files.get("delivery")
    if not file or file.filename == "":
        flash("Please choose a file to deliver.", "error")
        return redirect("/admin")

    safe_name = secure_filename(file.filename)
    if not safe_name:
        flash("Invalid filename.", "error")
        return redirect("/admin")

    filename = f"project_{project_id}_{int(datetime.now().timestamp())}_{safe_name}"
    os.makedirs(app.config["DELIVERY_FOLDER"], exist_ok=True)
    file.save(os.path.join(app.config["DELIVERY_FOLDER"], filename))

    conn = get_db_connection()
    project = conn.execute(
        "SELECT * FROM projects WHERE id=?",
        (project_id,),
    ).fetchone()

    if project is None:
        conn.close()
        return redirect("/admin")

    conn.execute(
        """
        UPDATE projects
        SET delivery_file=?, status='Delivered'
        WHERE id=?
        """,
        (filename, project_id),
    )

    if project["user_id"]:
        conn.execute(
            """
            INSERT INTO notifications(
                user_id, project_id, title, description, is_read, created_at
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                project["user_id"],
                project_id,
                "Project Delivered",
                "Your project has been completed. You can now download the final files from your dashboard.",
                0,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

    conn.commit()
    conn.close()

    config.notify_client(
        project["email"],
        f"Your Project #{project_id} Is Ready for Download — {config.STUDIO_NAME}",
        f"""
        <div style="font-family:Inter,Arial,sans-serif;padding:24px;background:#0b0d15;color:#eef2ff;border-radius:12px;">
            <h2 style="margin-top:0;">Your Final Files Are Ready!</h2>
            <p>Hi {project['name']},</p>
            <p>Great news — your <strong>{project['service_name']} ({project['package_name']})</strong> project (#{project_id}) has been delivered.</p>
            <p>Log in to your client dashboard to download your completed files.</p>
            <p style="color:#9ca3af;font-size:13px;">— {config.STUDIO_NAME}</p>
        </div>
        """,
        f"Hi {project['name']}, your project #{project_id} has been delivered. Log in to your dashboard to download it.",
    )

    flash(f"Project #{project_id} delivered successfully.", "success")
    return redirect("/admin")


@app.route("/download/<filename>")
def download(filename):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(app.config["DELIVERY_FOLDER"], safe_name)
    if not os.path.exists(file_path):
        abort(404)

    if not session.get("admin_logged_in"):
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")
        conn = get_db_connection()
        project = conn.execute(
            "SELECT id FROM projects WHERE delivery_file=? AND user_id=?",
            (safe_name, user_id),
        ).fetchone()
        conn.close()
        if project is None:
            abort(403)

    return send_from_directory(
        app.config["DELIVERY_FOLDER"],
        safe_name,
        as_attachment=True,
    )


@app.route("/uploads/<filename>")
def download_upload(filename):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    if not os.path.exists(file_path):
        abort(404)

    if not session.get("admin_logged_in"):
        user_id = session.get("user_id")
        if not user_id:
            return redirect("/login")
        conn = get_db_connection()
        project = conn.execute(
            "SELECT id FROM projects WHERE filename=? AND user_id=?",
            (safe_name, user_id),
        ).fetchone()
        conn.close()
        if project is None:
            abort(403)

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        safe_name,
        as_attachment=True,
    )


@app.context_processor
def inject_keys():
    return {
        "RAZORPAY_KEY_ID": config.RAZORPAY_KEY_ID,
        "OWNER_EMAIL": config.OWNER_EMAIL or "contact@vikasstudio.com",
        "STUDIO_NAME": config.STUDIO_NAME,
        "year": datetime.now().year,
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
