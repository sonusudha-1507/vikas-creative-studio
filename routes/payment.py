from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    jsonify,
    session
)

from datetime import datetime

import os
import razorpay

from models.database import get_db_connection

payment_bp = Blueprint("payment", __name__)

razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)


# ---------------------------------------
# PAYMENT PAGE
# ---------------------------------------

@payment_bp.route("/pay/<int:project_id>")
def pay(project_id):

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
        return "Project not found",404

    try:

        amount = int(project["price"])

    except:

        amount = 0

    if amount <= 0:
        return "Invalid project price",400

    razorpay_order = razorpay_client.order.create({

        "amount": amount * 100,

        "currency": "INR",

        "payment_capture": 1

    })

    return render_template(

        "payment.html",

        project=project,

        order=razorpay_order,

        key=os.getenv("RAZORPAY_KEY_ID")

    )


# ---------------------------------------
# PAYMENT SUCCESS
# ---------------------------------------

@payment_bp.route(
    "/payment-success/<int:project_id>",
    methods=["POST"]
)
def payment_success(project_id):

    data = request.get_json()

    payment_id = data.get("payment_id")

    conn = get_db_connection()

    project = conn.execute(

        """
        SELECT *
        FROM projects
        WHERE id=?
        """,

        (project_id,)

    ).fetchone()

    if project is None:

        conn.close()

        return jsonify(
            {
                "success":False
            }
        )

    conn.execute(

        """
        UPDATE projects

        SET

        payment_status=?,

        payment_id=?

        WHERE id=?

        """,

        (

            "Paid",

            payment_id,

            project_id

        )

    )
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
        project["user_id"],
        project_id,
        "Payment Successful",
        "Your payment has been received successfully.",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
)
    
    conn.execute(

        """
        INSERT INTO payments(

            project_id,

            user_id,

            razorpay_payment_id,

            amount,

            status,

            created_at

        )

        VALUES(

            ?,?,?,?,?,?

        )

        """,

        (

            project_id,

            project["user_id"],

            payment_id,

            project["price"],

            "Success",

            datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        )

    )

    conn.commit()

    conn.close()

    return jsonify(

    {

        "success": True,

        "redirect": f"/thank-you/{project_id}"

    }

)


# ---------------------------------------
# CREATE ORDER API
# ---------------------------------------

@payment_bp.route(
    "/create-payment",
    methods=["POST"]
)
def create_payment():

    amount = int(request.form.get("price"))

    razorpay_order = razorpay_client.order.create({

        "amount": amount * 100,

        "currency":"INR",

        "payment_capture":1

    })

    return jsonify(razorpay_order)

