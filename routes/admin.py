from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for
)

from models.database import get_db_connection

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


@admin_bp.route("/update-status/<int:project_id>", methods=["POST"])
def update_status(project_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    status = request.form.get("status")

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE projects
        SET status=?
        WHERE id=?
        """,
        (status, project_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
