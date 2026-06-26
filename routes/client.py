from flask import Blueprint, render_template, redirect, session
from models.database import get_db_connection

client_bp = Blueprint("client", __name__)


@client_bp.route("/client-dashboard")
def client_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    projects = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE user_id=?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "client_dashboard.html",
        projects=projects
    )


@client_bp.route("/track-project")
def track_project():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    projects = conn.execute(
        """
        SELECT *
        FROM projects
        WHERE user_id=?
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "track_project.html",
        projects=projects
    )
