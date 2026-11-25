from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("signup.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        flash("Please fill in all fields.", "error")
        return redirect("/signup")

    if len(password) < 6:
        flash("Password must be at least 6 characters.", "error")
        return redirect("/signup")

    conn = get_db_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE email=?",
        (email,),
    ).fetchone()

    if existing:
        conn.close()
        flash("Email is already registered. Please login.", "error")
        return redirect("/signup")

    conn.execute(
        """
        INSERT INTO users(name, email, password, created_at)
        VALUES(?,?,?,?)
        """,
        (
            name,
            email,
            generate_password_hash(password),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    conn.close()

    flash("Account created successfully! Please login.", "success")
    return redirect("/login")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email=?",
        (email,),
    ).fetchone()
    conn.close()

    if user is None or not check_password_hash(user["password"], password):
        flash("Invalid email or password.", "error")
        return redirect("/login")

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    flash(f"Welcome back, {user['name']}!", "success")
    return redirect("/dashboard")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect("/")
