from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from models.database import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO users
            (name, email, password, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                request.form["name"],
                request.form["email"],
                generate_password_hash(request.form["password"]),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (request.form["email"],)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            request.form["password"]
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/client-dashboard")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/")
