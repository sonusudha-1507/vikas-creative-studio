from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

from datetime import datetime

from models.database import get_db_connection

services_bp = Blueprint("services", __name__)


# ---------------------------------
# HOME
# ---------------------------------

@services_bp.route("/")
def home():

    return render_template(
        "home.html",
        year=datetime.now().year
    )


# ---------------------------------
# SERVICES
# ---------------------------------

SERVICES = {

    "photo-editing":{

        "title":"Photo Editing",

        "description":"Professional photo retouching.",

        "packages":{

            "Basic":999,

            "Premium":2499,

            "Ultimate":4999

        }

    },


    "video-editing":{

        "title":"Video Editing",

        "description":"Professional cinematic editing.",

        "packages":{

            "Basic":1999,

            "Premium":4999,

            "Ultimate":8999

        }

    },


    "reels-editing":{

        "title":"Reels Editing",

        "description":"Instagram Reels and Shorts.",

        "packages":{

            "Basic":799,

            "Premium":1799,

            "Ultimate":2999

        }

    },


    "thumbnail-design":{

        "title":"Thumbnail Design",

        "description":"YouTube Thumbnail Design.",

        "packages":{

            "Basic":399,

            "Premium":699,

            "Ultimate":999

        }

    }

}


# ---------------------------------
# SERVICES PAGE
# ---------------------------------

@services_bp.route("/services")
def services():

    return render_template(

        "services.html",

        services=SERVICES,

        year=datetime.now().year

    )


# ---------------------------------
# SERVICE DETAILS
# ---------------------------------

@services_bp.route("/services/<service_slug>")
def service_detail(service_slug):

    service = SERVICES.get(service_slug)

    if service is None:

        return "Service Not Found",404

    return render_template(

        "service_detail.html",

        service=service,

        service_slug=service_slug,

        year=datetime.now().year

    )


# ---------------------------------
# START PROJECT
# ---------------------------------
@services_bp.route("/start-project", methods=["GET", "POST"])
def start_project():

    if request.method == "GET":

        return render_template(

            "start_project.html",

            service=request.args.get("service"),

            package=request.args.get("package"),

            price=request.args.get("price"),

            year=datetime.now().year

        )

    # ----------------------------------------
    # Form Data
    # ----------------------------------------

    name = request.form.get("name", "").strip()

    email = request.form.get("email", "").strip()

    project_type = request.form.get("project_type", "").strip()

    description = request.form.get("description", "").strip()

    service = request.form.get("service", "").strip()

    package = request.form.get("package", "").strip()

    price = request.form.get("price", "0").strip()

    if not name or not email or not service:

        return "Missing required fields.", 400

    try:

        price = int(price)

    except ValueError:

        return "Invalid price.", 400

    # ----------------------------------------
    # Upload File
    # ----------------------------------------

    filename = None

    uploaded_file = request.files.get("project_file")

    if uploaded_file and uploaded_file.filename:

        from werkzeug.utils import secure_filename

        import os

        os.makedirs("uploads", exist_ok=True)

        filename = secure_filename(uploaded_file.filename)

        uploaded_file.save(

            os.path.join(

                "uploads",

                filename

            )

        )

    # ----------------------------------------
    # Save Project
    # ----------------------------------------

    conn = get_db_connection()

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
            payment_status,
            user_id,
            created_at

        )

        VALUES(

            ?,?,?,?,?,?,?,?,?,?,?

        )
        """,

        (

            name,
            email,
            project_type,
            description,
            filename,
            service,
            package,
            price,
            "Pending",
            session.get("user_id"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

    )

    project_id = cursor.lastrowid

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

            ?,?,?,?,?

        )
        """,

        (

            session.get("user_id"),
            project_id,
            "Project Submitted",
            f"Your {service} project has been submitted successfully.",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

    )

    conn.commit()

    conn.close()

    return redirect(

        f"/pay/{project_id}"

    )

# ---------------------------------
# THANK YOU
# ---------------------------------

@services_bp.route("/thank-you/<int:project_id>")
def thank_you(project_id):

    conn = get_db_connection()

    project = conn.execute(

        """
        SELECT *
        FROM projects
        WHERE id=?
        """,

        (project_id,)

    ).fetchone()

    conn.close()

    if project is None:

        return "Project not found", 404

    return render_template(

        "thank_you.html",

        project=project,

        year=datetime.now().year

    )