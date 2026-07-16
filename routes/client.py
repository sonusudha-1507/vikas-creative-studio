from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    jsonify
)

from models.database import get_db_connection

client_bp = Blueprint("client", __name__)


# ---------------------------------------------------
# CLIENT DASHBOARD
# ---------------------------------------------------

@client_bp.route("/dashboard")
def dashboard():

    if not session.get("user_id"):
        return redirect("/login")

    conn = get_db_connection()

    projects = conn.execute(
        """
        SELECT *

        FROM projects

        WHERE user_id=?

        ORDER BY id DESC
        """,
        (
            session["user_id"],
        )
    ).fetchall()

    notifications = conn.execute(
        """
        SELECT *

        FROM notifications

        WHERE user_id=?

        ORDER BY id DESC

        LIMIT 10
        """,
        (
            session["user_id"],
        )
    ).fetchall()

    unread = conn.execute(
        """
        SELECT COUNT(*) total

        FROM notifications

        WHERE

            user_id=?
            AND is_read=0
        """,
        (
            session["user_id"],
        )
    ).fetchone()["total"]

    conn.close()

    return render_template(

        "client_dashboard.html",

        projects=projects,

        notifications=notifications,

        unread=unread

    )


# ---------------------------------------------------
# PROFILE
# ---------------------------------------------------

@client_bp.route("/profile")
def profile():

    if not session.get("user_id"):
        return redirect("/login")

    conn = get_db_connection()

    user = conn.execute(
        """
        SELECT *

        FROM users

        WHERE id=?
        """,
        (
            session["user_id"],
        )
    ).fetchone()

    conn.close()

    return render_template(

        "profile.html",

        user=user

    )


# ---------------------------------------------------
# NOTIFICATION API
# ---------------------------------------------------

@client_bp.route("/notifications")
def notifications():

    if not session.get("user_id"):
        return jsonify([])

    conn = get_db_connection()

    rows = conn.execute(
        """
        SELECT *

        FROM notifications

        WHERE user_id=?

        ORDER BY id DESC
        """,
        (
            session["user_id"],
        )
    ).fetchall()

    conn.close()

    return jsonify([

        {

            "title":row["title"],

            "description":row["description"],

            "created_at":row["created_at"],

            "is_read":row["is_read"]

        }

        for row in rows

    ])


# ---------------------------------------------------
# MARK ALL READ
# ---------------------------------------------------

@client_bp.route("/notifications/read")
def mark_notifications_read():

    if not session.get("user_id"):
        return redirect("/login")

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE notifications

        SET is_read=1

        WHERE user_id=?
        """,
        (
            session["user_id"],
        )
    )

    conn.commit()

    conn.close()

    return redirect("/dashboard")