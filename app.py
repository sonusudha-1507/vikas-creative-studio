from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from datetime import datetime

import sqlite3
import os
import razorpay
from dotenv import load_dotenv
from routes.auth import auth_bp
from routes.client import client_bp
from routes.admin import admin_bp

load_dotenv()
# =====================================
# APP CONFIG
# =====================================

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(client_bp)
app.register_blueprint(admin_bp)

app.secret_key = "vikas-secret-key"


# Razorpay test config

razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)

# Admin

ADMIN_USERNAME = "vikas"
ADMIN_PASSWORD = "vikas123"



# =====================================
# FILE CONFIG
# =====================================

UPLOAD_FOLDER = "uploads"

DELIVERY_FOLDER = "deliveries"


ALLOWED_EXTENSIONS = {

    "png",
    "jpg",
    "jpeg",
    "mp4",
    "mov",
    "zip",
    "pdf"

}


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["DELIVERY_FOLDER"] = DELIVERY_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    200 * 1024 * 1024
)



def allowed_file(filename):

    return (

        "." in filename

        and

        filename.rsplit(
            ".",
            1
        )[1].lower()

        in ALLOWED_EXTENSIONS

    )



# =====================================
# DATABASE
# =====================================

DB_PATH = "database/projects.db"



def get_db_connection():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn




def init_db():

    conn = get_db_connection()

    cursor = conn.cursor()



    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS projects(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        email TEXT,

        project_type TEXT,

        description TEXT,

        filename TEXT,

        service_name TEXT,

        package_name TEXT,

        price INTEGER,


        user_id INTEGER,


        delivery_file TEXT,


        status TEXT DEFAULT 'Submitted',


        created_at TEXT

    )


    """
    )



    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        created_at TEXT NOT NULL

    )

    """
    )




    cursor.execute(
    """

    CREATE TABLE IF NOT EXISTS messages(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        project_id INTEGER NOT NULL,

        sender TEXT NOT NULL,

        message TEXT NOT NULL,

        created_at TEXT NOT NULL

    )

    """
    )

    cursor.execute("""
CREATE TABLE IF NOT EXISTS payments(

id INTEGER PRIMARY KEY AUTOINCREMENT,

project_id INTEGER,

user_id INTEGER,

razorpay_payment_id TEXT,

amount INTEGER,

status TEXT,

created_at TEXT

)
""")

    conn.commit()

    conn.close()



# =====================================
# BASIC ROUTES
# =====================================


@app.route("/")
def home():

    return render_template(

        "home.html",

        year=datetime.now().year

    )



@app.route("/services")
def services():

    return render_template(

        "services.html",

        year=datetime.now().year

    )




@app.route("/services/<service_name>")
def service_detail(service_name):


    services={


        "photo-editing":{

            "title":"Photo Editing",

            "description":
            "Professional photo retouching and creative edits"

        },


        "video-editing":{

            "title":"Video Editing",

            "description":
            "Cinematic storytelling video edits"

        },



        "reels-editing":{

            "title":"Reels Editing",

            "description":
            "High retention short form content"

        },



        "thumbnail-design":{

            "title":"Thumbnail Design",

            "description":
            "Creative thumbnails and posters"

        }


    }



    service=services.get(service_name)



    if not service:

        return "Service not found",404



    return render_template(

        "service_detail.html",

        service=service,

        service_slug=service_name,

        year=datetime.now().year

    )
# =====================================
# START PROJECT / ORDER
# =====================================

@app.route("/start-project", methods=["GET","POST"])
def start_project():

    if request.method=="POST":

        name=request.form.get("name")
        email=request.form.get("email")
        project_type=request.form.get("project_type")
        description=request.form.get("description")

        service_name=request.form.get("service")
        package_name=request.form.get("package")
        price=request.form.get("price")


        file=request.files.get("project_file")

        filename=None


        if file and allowed_file(file.filename):

            filename=secure_filename(
                file.filename
            )


            file.save(

                os.path.join(

                    app.config["UPLOAD_FOLDER"],

                    filename

                )

            )


        conn=get_db_connection()


        cursor = conn.execute(
        """

        INSERT INTO projects(

            name,
            email,
            project_type,
            description,
            filename,
            service_name,
            package_name,
            price,
            user_id,
            created_at

        )

        VALUES(?,?,?,?,?,?,?,?,?,?)

        """,

        (

            name,
            email,
            project_type,
            description,
            filename,
            service_name,
            package_name,
            price,
            session.get("user_id"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

        )


        conn.commit()

        conn.close()


        return redirect(
    f"/pay/{cursor.lastrowid}"
)


    return render_template(

        "start_project.html",

        service=request.args.get("service"),

        package=request.args.get("package"),

        price=request.args.get("price")

    )




@app.route("/thank-you")
def thank_you():

    return render_template(
        "thank_you.html"
    )



# =====================================
# ADMIN
# =====================================


@app.route("/admin-login", methods=["GET","POST"])
def admin_login():


    if request.method=="POST":


        if (

        request.form.get("username")==ADMIN_USERNAME

        and

        request.form.get("password")==ADMIN_PASSWORD

        ):


            session["admin_logged_in"]=True


            return redirect("/admin")



    return render_template(
        "admin_login.html"
    )




@app.route("/admin")
def admin():


    if not session.get("admin_logged_in"):

        return redirect("/admin-login")



    conn=get_db_connection()



    projects=conn.execute(

        "SELECT * FROM projects ORDER BY created_at DESC"

    ).fetchall()



    conn.close()



    return render_template(

        "admin.html",

        projects=projects

    )




@app.route("/update-status/<int:project_id>",methods=["POST"])
def update_status(project_id):


    conn=get_db_connection()


    conn.execute(

        "UPDATE projects SET status=? WHERE id=?",

        (

        request.form.get("status"),

        project_id

        )

    )


    conn.commit()

    conn.close()


    return redirect("/admin")





# =====================================
# CHAT SYSTEM
# =====================================


@app.route("/project/<int:project_id>/chat",
methods=["GET","POST"])
def chat(project_id):


    conn=get_db_connection()


    if request.method=="POST":


        sender=session.get(

            "user_name",

            "Vikas"

        )


        conn.execute(

        """

        INSERT INTO messages(

        project_id,

        sender,

        message,

        created_at

        )

        VALUES(?,?,?,?)

        """,

        (

        project_id,

        sender,

        request.form.get("message"),

        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

        )


        conn.commit()



    messages=conn.execute(

    "SELECT * FROM messages WHERE project_id=?",

    (project_id,)

    ).fetchall()



    conn.close()



    return render_template(

        "chat.html",

        messages=messages

    )

@app.route(
"/admin/project/<int:project_id>/chat",
methods=["GET","POST"]
)
def admin_project_chat(project_id):


    if not session.get("admin_logged_in"):

        return redirect("/admin-login")



    conn=get_db_connection()



    if request.method=="POST":


        conn.execute(

        """

        INSERT INTO messages(

        project_id,

        sender,

        message,

        created_at

        )

        VALUES(?,?,?,?)

        """,

        (

        project_id,

        "Vikas",

        request.form.get("message"),

        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

        )


        conn.commit()




    messages=conn.execute(

        """

        SELECT *

        FROM messages

        WHERE project_id=?

        ORDER BY created_at

        """,

        (

        project_id,

        )

    ).fetchall()



    conn.close()



    return render_template(

        "chat.html",

        messages=messages,

        project_id=project_id

    )



# =====================================
# DELIVERY SYSTEM
# =====================================


@app.route("/deliver/<int:project_id>", methods=["POST"])
def deliver_project(project_id):


    file=request.files.get("delivery")



    if file and file.filename:


        filename=secure_filename(
            file.filename
        )


        file.save(

        os.path.join(

            app.config["DELIVERY_FOLDER"],

            filename

        )

        )



        conn=get_db_connection()


        conn.execute(

        """

        UPDATE projects

        SET delivery_file=?,

        status='Delivered'

        WHERE id=?

        """,

        (

        filename,

        project_id

        )

        )


        conn.commit()

        conn.close()


        print(
            "DELIVERY SAVED:",
            filename
        )



    return redirect("/admin")





@app.route("/download/<filename>")
def download(filename):


    return send_from_directory(

        app.config["DELIVERY_FOLDER"],

        filename,

        as_attachment=True

    )





# =====================================
# RAZORPAY FOUNDATION
# =====================================


@app.route("/create-payment",methods=["POST"])
def create_payment():


    order=razorpay_client.order.create({

        "amount":
        int(request.form.get("price"))*100,

        "currency":"INR",

        "payment_capture":1

    })



    return render_template(

        "payment.html",

        order=order

    )
@app.route("/pay/<int:project_id>")
def pay(project_id):


    conn=get_db_connection()


    project=conn.execute(

        "SELECT * FROM projects WHERE id=?",

        (project_id,)

    ).fetchone()


    conn.close()



    order=razorpay_client.order.create({

        "amount":

        int(project["price"] if project["price"] not in [None,"None"] else 0) * 100,


        "currency":

        "INR",


        "payment_capture":

        1

    })



    return render_template(

        "payment.html",

        project=project,

        order=order,

        key=os.getenv(
            "RAZORPAY_KEY_ID"
        )

    )
@app.route(
"/payment-success/<int:project_id>",
methods=["POST"]
)
def payment_success(project_id):


    data=request.json


    conn=get_db_connection()


    conn.execute(

    """

    UPDATE projects

    SET

    payment_status='Paid',

    payment_id=?

    WHERE id=?

    """,

    (

    data["payment_id"],

    project_id

    )

    )


    conn.commit()

    conn.close()


    return "success"




# =====================================
# START SERVER
# =====================================


if __name__=="__main__":


    os.makedirs(
        "uploads",
        exist_ok=True
    )


    os.makedirs(
        "deliveries",
        exist_ok=True
    )


    os.makedirs(
        "database",
        exist_ok=True
    )


    init_db()


    app.run(
        debug=True
    )