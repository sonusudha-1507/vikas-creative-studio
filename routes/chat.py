from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

from datetime import datetime

from models.database import get_db_connection

chat_bp = Blueprint("chat", __name__)


def load_messages(project_id):

    conn = get_db_connection()

    messages = conn.execute(
        """
        SELECT *
        FROM messages
        WHERE project_id=?
        ORDER BY created_at
        """,
        (project_id,)
    ).fetchall()

    conn.close()

    return messages


@chat_bp.route(
    "/project/<int:project_id>/chat",
    methods=["GET", "POST"]
)
def client_chat(project_id):

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO messages
            (
                project_id,
                sender,
                message,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                project_id,
                session["user_name"],
                request.form["message"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

    return render_template(
        "chat.html",
        project_id=project_id,
        messages=load_messages(project_id)
    )


@chat_bp.route(
    "/admin/project/<int:project_id>/chat",
    methods=["GET", "POST"]
)
def admin_chat(project_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    if request.method == "POST":

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO messages
            (
                project_id,
                sender,
                message,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                project_id,
                "Vikas",
                request.form["message"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

    return render_template(
        "chat.html",
        project_id=project_id,
        messages=load_messages(project_id)
    )
