from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash
)

from datetime import datetime

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from models.database import get_db_connection

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------

@auth_bp.route("/signup", methods=["GET", "POST"])
def register():

    if request.method == "GET":

        return render_template("signup.html")

    name = request.form.get("name", "").strip()

    email = request.form.get("email", "").strip().lower()

    password = request.form.get("password", "")

    if not name or not email or not password:

        flash("Please fill all fields.", "error")

        return redirect("/signup")

    conn = get_db_connection()

    existing = conn.execute(

        """
        SELECT id

        FROM users

        WHERE email=?
        """,

        (
            email,
        )

    ).fetchone()

    if existing:

        conn.close()

        flash("Email already registered.", "error")

        return redirect("/signup")

    conn.execute(

        """
        INSERT INTO users(

            name,
            email,
            password,
            created_at

        )

        VALUES(

            ?,?,?,?

        )
        """,

        (

            name,
            email,
            generate_password_hash(password),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

    )

    conn.commit()

    conn.close()

    flash("Registration successful. Please login.", "success")

    return redirect("/login")


# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()

    password = request.form.get("password", "")

    conn = get_db_connection()

    user = conn.execute(

        """
        SELECT *

        FROM users

        WHERE email=?
        """,

        (
            email,
        )

    ).fetchone()

    conn.close()
    # debug prints (optional)
    # print("EMAIL ENTERED:", email)
    # print("USER FOUND:", user is not None)
    print("EMAIL ENTERED:", email)

    print("USER FOUND:", user is not None)

    if user:

     print("DB EMAIL:", user["email"])

     password_ok = check_password_hash(user["password"], password)

     print("PASSWORD CHECK:", password_ok)

    else:

     password_ok = False


    if user is None:

     flash("User not found", "error")
     return redirect("/login")


    if not password_ok:

     flash("Wrong password", "error")

     return redirect("/login")

    # Successful login: set session and redirect
    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]

    flash(f"Welcome back, {user['name']}!", "success")
    return redirect("/dashboard")




# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/")