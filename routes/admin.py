import hmac
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for,
    flash,
)

import config
from models.database import get_db_connection

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not config.ADMIN_PASSWORD:
            error = "ADMIN_PASSWORD is not configured in environment variables."
        elif hmac.compare_digest(username, config.ADMIN_USERNAME) and hmac.compare_digest(
            password, config.ADMIN_PASSWORD
        ):
            session["admin_logged_in"] = True
            return redirect(url_for("admin.admin_dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@admin_bp.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin-login")


@admin_bp.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    conn = get_db_connection()
    projects = conn.execute(
        """
        SELECT *
        FROM projects
        ORDER BY id DESC
        """
    ).fetchall()

    clients = conn.execute(
        """
        SELECT
            MAX(name) AS name,
            LOWER(email) AS email,
            COUNT(*) AS total_projects,
            SUM(CASE WHEN payment_status='Paid' THEN 1 ELSE 0 END) AS paid_projects,
            COALESCE(SUM(CASE WHEN payment_status='Paid' THEN price ELSE 0 END), 0) AS total_spent
        FROM projects
        GROUP BY LOWER(email)
        ORDER BY MAX(id) DESC
        """
    ).fetchall()

    total_revenue = sum(
        (p["price"] or 0) for p in projects if p["payment_status"] == "Paid"
    )
    conn.close()

    return render_template(
        "admin.html",
        projects=projects,
        clients=clients,
        total_revenue=total_revenue,
    )


@admin_bp.route("/project/<int:project_id>/status", methods=["POST"])
def update_project_status(project_id):
    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    status = request.form.get("status", "Submitted").strip()
    allowed_statuses = {"Submitted", "Reviewing", "Editing", "Rendering", "Delivered"}
    if status not in allowed_statuses:
        flash("Invalid status.", "error")
        return redirect("/admin")

    conn = get_db_connection()
    project = conn.execute(
        "SELECT * FROM projects WHERE id=?",
        (project_id,),
    ).fetchone()

    if project is None:
        conn.close()
        return redirect("/admin")

    conn.execute(
        "UPDATE projects SET status=? WHERE id=?",
        (status, project_id),
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
                "Project Status Updated",
                f"Your project #{project_id} is now '{status}'.",
                0,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

    conn.commit()
    conn.close()

    flash(f"Project #{project_id} status updated to {status}.", "success")
    return redirect("/admin")
