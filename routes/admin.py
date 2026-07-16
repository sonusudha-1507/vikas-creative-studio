from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for
)

from models.database import get_db_connection
from datetime import datetime


admin_bp = Blueprint("admin", __name__)

ADMIN_USERNAME = "vikas"
ADMIN_PASSWORD = "vikas123"


@admin_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        if (
            request.form.get("username") == ADMIN_USERNAME
            and
            request.form.get("password") == ADMIN_PASSWORD
        ):

            session["admin_logged_in"] = True

            return redirect(url_for("admin.admin_dashboard"))

    return render_template("admin_login.html")


@admin_bp.route("/admin")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    conn = get_db_connection()

    projects = conn.execute(
        """
        SELECT *
        FROM projects
        ORDER BY created_at DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        projects=projects
    )


@admin_bp.route("/project/<int:project_id>/status", methods=["POST"])
def update_project_status(project_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    status = request.form.get("status")

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

        SET status=?

        WHERE id=?
        """,
        (
            status,
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

            ?,?,?,?,?,?

        )
        """,
        (
            project["user_id"],
            project_id,
            "Project Status Updated",
            f"Your project is now '{status}'.",
            0,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()

    conn.close()

    return redirect("/admin")
