from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session,
    redirect
)

from datetime import datetime

from models.database import get_db_connection

chat_bp = Blueprint("chat", __name__)


# --------------------------------------------------
# CLIENT CHAT PAGE
# --------------------------------------------------

@chat_bp.route("/chat/<int:project_id>")
def chat(project_id):

    if not session.get("user_id"):
        return redirect("/login")

    conn = get_db_connection()

    project = conn.execute(
        """
        SELECT *

        FROM projects

        WHERE id=?
        AND user_id=?
        """,
        (
            project_id,
            session["user_id"]
        )
    ).fetchone()

    if project is None:
        conn.close()
        return "Project not found",404

    messages = conn.execute(
        """
        SELECT *

        FROM messages

        WHERE project_id=?

        ORDER BY id
        """,
        (
            project_id,
        )
    ).fetchall()

    conn.execute(
        """
        UPDATE messages

        SET is_read=1

        WHERE
            project_id=?
            AND sender='Admin'
        """,
        (
            project_id,
        )
    )

    conn.commit()
    conn.close()

    return render_template(
        "chat.html",
        project=project,
        messages=messages
    )


# --------------------------------------------------
# ADMIN CHAT
# --------------------------------------------------

@chat_bp.route("/admin/chat")
def admin_chat():

    if not session.get("admin_logged_in"):
        return redirect("/admin-login")

    conn = get_db_connection()

    projects = conn.execute(
        """
        SELECT

            p.*,

            (
                SELECT COUNT(*)

                FROM messages

                WHERE

                    project_id=p.id
                    AND sender='Client'
                    AND is_read=0

            ) unread

        FROM projects p

        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(

        "admin_chat.html",

        projects=projects

    )


# --------------------------------------------------
# ADMIN LOAD CHAT
# --------------------------------------------------

@chat_bp.route("/admin/chat/<int:project_id>")
def admin_chat_messages(project_id):

    if not session.get("admin_logged_in"):
        return jsonify([])

    conn = get_db_connection()

    rows = conn.execute(
        """
        SELECT *

        FROM messages

        WHERE project_id=?

        ORDER BY id
        """,
        (
            project_id,
        )
    ).fetchall()

    conn.execute(
        """
        UPDATE messages

        SET is_read=1

        WHERE

            project_id=?
            AND sender='Client'
        """,
        (
            project_id,
        )
    )

    conn.commit()

    conn.close()

    return jsonify([

        {

            "id":row["id"],

            "sender":row["sender"],

            "message":row["message"],

            "created_at":row["created_at"]

        }

        for row in rows

    ])


# --------------------------------------------------
# CLIENT SEND
# --------------------------------------------------

@chat_bp.route(
    "/chat/send/<int:project_id>",
    methods=["POST"]
)
def send_message(project_id):

    if not session.get("user_id"):
        return jsonify(success=False)

    message=request.form.get("message","").strip()

    if message=="":
        return jsonify(success=False)

    conn=get_db_connection()

    conn.execute(
        """
        INSERT INTO messages(

            project_id,

            sender,

            message,

            is_read,

            created_at

        )

        VALUES(

            ?,?,?,?,?

        )
        """,
        (
            project_id,
            "Client",
            message,
            0,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()

    return jsonify(success=True)


# --------------------------------------------------
# ADMIN SEND
# --------------------------------------------------

@chat_bp.route(
    "/admin/chat/send/<int:project_id>",
    methods=["POST"]
)
def admin_send(project_id):

    if not session.get("admin_logged_in"):
        return jsonify(success=False)

    message=request.form.get("message","").strip()

    if message=="":
        return jsonify(success=False)

    conn=get_db_connection()

    conn.execute(
        """
        INSERT INTO messages(

            project_id,

            sender,

            message,

            is_read,

            created_at

        )

        VALUES(

            ?,?,?,?,?

        )
        """,
        (
            project_id,
            "Admin",
            message,
            0,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()

    return jsonify(success=True)


# --------------------------------------------------
# FETCH CLIENT CHAT
# --------------------------------------------------

@chat_bp.route("/chat/messages/<int:project_id>")
def fetch_messages(project_id):

    conn=get_db_connection()

    rows=conn.execute(
        """
        SELECT *

        FROM messages

        WHERE project_id=?

        ORDER BY id
        """,
        (
            project_id,
        )
    ).fetchall()

    conn.close()

    return jsonify([

        {

            "id":row["id"],

            "sender":row["sender"],

            "message":row["message"],

            "created_at":row["created_at"]

        }

        for row in rows

    ])


# --------------------------------------------------
# UNREAD COUNTER
# --------------------------------------------------

"""
@chat_bp.route("/admin/unread-count")
def unread_count():

    if not session.get("admin_logged_in"):
        return jsonify({"count":0})

    conn=get_db_connection()

    total=conn.execute(
        '''
        SELECT COUNT(*) total

        FROM messages

        WHERE

            sender='Client'
            AND is_read=0
        '''
    ).fetchone()["total"]

    conn.close()

    return jsonify({"count":total})
"""