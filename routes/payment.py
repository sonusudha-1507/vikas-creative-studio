import hmac
import hashlib
import json
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    jsonify,
    session,
    flash,
)
import razorpay

import config
from models.database import get_db_connection

payment_bp = Blueprint("payment", __name__)


def get_razorpay_client():
    key_id = (config.RAZORPAY_KEY_ID or "").strip()
    key_secret = (config.RAZORPAY_KEY_SECRET or "").strip()
    if not (key_id and key_secret):
        return None
    return razorpay.Client(auth=(key_id, key_secret))


def mark_project_paid(project_id, payment_id):
    conn = get_db_connection()
    project = conn.execute(
        "SELECT * FROM projects WHERE id=?",
        (project_id,),
    ).fetchone()

    if project is None:
        conn.close()
        return None

    if project["payment_status"] == "Paid":
        conn.close()
        return project

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        """
        UPDATE projects
        SET payment_status=?, payment_id=?
        WHERE id=?
        """,
        ("Paid", payment_id, project_id),
    )

    if project["user_id"]:
        conn.execute(
            """
            INSERT INTO notifications(
                user_id, project_id, title, description, is_read, created_at
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                project["user_id"],
                project_id,
                "Payment Successful",
                f"Payment of ₹{project['price']} received. Our studio has started reviewing your project.",
                0,
                now_str,
            ),
        )

    conn.execute(
        """
        INSERT INTO payments(
            project_id, user_id, razorpay_payment_id, amount, status, created_at
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            project_id,
            project["user_id"],
            payment_id,
            project["price"],
            "Success",
            now_str,
        ),
    )

    conn.commit()
    conn.close()

    config.notify_owner(
        f"Payment Received ₹{project['price']} — Project #{project_id}",
        f"""
        <div style="font-family:Inter,Arial,sans-serif;padding:24px;background:#0b0d15;color:#eef2ff;border-radius:12px;">
            <h2 style="margin-top:0;color:#22c55e;">Payment Received — ₹{project['price']}</h2>
            <p><strong>Project ID:</strong> #{project_id}</p>
            <p><strong>Client:</strong> {project['name']} ({project['email']})</p>
            <p><strong>Service:</strong> {project['service_name']} — {project['package_name']}</p>
            <p><strong>Razorpay Payment ID:</strong> {payment_id}</p>
            <p><strong>Brief:</strong><br>{project['description']}</p>
            <p><strong>Client Upload:</strong> {project['filename'] or 'None'}</p>
        </div>
        """,
        f"Payment received: ₹{project['price']} for Project #{project_id} ({project['service_name']}) from {project['name']}. Payment ID: {payment_id}",
    )

    config.notify_client(
        project["email"],
        f"Order Confirmed (#{project_id}) — {config.STUDIO_NAME}",
        f"""
        <div style="font-family:Inter,Arial,sans-serif;padding:24px;background:#0b0d15;color:#eef2ff;border-radius:12px;">
            <h2 style="margin-top:0;">Thank You, {project['name']}!</h2>
            <p>Your payment of <strong>₹{project['price']}</strong> has been confirmed.</p>
            <p><strong>Project ID:</strong> #{project_id}<br>
               <strong>Service:</strong> {project['service_name']} ({project['package_name']})<br>
               <strong>Payment ID:</strong> {payment_id}</p>
            <p>Our creative team is now reviewing your files and brief. You can track live progress or chat with us anytime from your dashboard.</p>
            <p style="color:#9ca3af;font-size:13px;">— {config.STUDIO_NAME}</p>
        </div>
        """,
        f"Thank you {project['name']}! Payment of ₹{project['price']} for Project #{project_id} is confirmed. Payment ID: {payment_id}",
    )

    return project


@payment_bp.route("/pay/<int:project_id>")
def pay(project_id):
    conn = get_db_connection()
    project = conn.execute(
        "SELECT * FROM projects WHERE id=?",
        (project_id,),
    ).fetchone()
    conn.close()

    if project is None:
        return "Project not found", 404

    if project["payment_status"] == "Paid":
        return redirect(f"/thank-you/{project_id}")

    try:
        amount = int(project["price"])
    except (TypeError, ValueError):
        amount = 0

    if amount <= 0:
        return "Invalid project price", 400

    client = get_razorpay_client()
    if client is None:
        flash(
            "Payment gateway is not configured yet. Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env.",
            "error",
        )
        return render_template(
            "payment.html",
            project=project,
            order=None,
            key="",
            gateway_error=True,
        )

    try:
        razorpay_order = client.order.create(
            {
                "amount": amount * 100,
                "currency": "INR",
                "receipt": f"project_{project_id}",
                "payment_capture": 1,
                "notes": {
                    "project_id": str(project_id),
                    "client_email": project["email"],
                    "service": f"{project['service_name']} - {project['package_name']}",
                },
            }
        )
    except Exception as exc:
        print("Razorpay order creation failed:", repr(exc))
        flash(f"Razorpay error: {exc}. Please check your API keys in .env.", "error")
        return render_template(
            "payment.html",
            project=project,
            order=None,
            key="",
            gateway_error=True,
        )

    session[f"rzp_order_{project_id}"] = razorpay_order["id"]

    return render_template(
        "payment.html",
        project=project,
        order=razorpay_order,
        key=config.RAZORPAY_KEY_ID.strip(),
        gateway_error=False,
    )


@payment_bp.route("/payment-success/<int:project_id>", methods=["POST"])
def payment_success(project_id):
    data = request.get_json(silent=True) or {}
    payment_id = data.get("razorpay_payment_id") or data.get("payment_id")
    order_id = data.get("razorpay_order_id")
    signature = data.get("razorpay_signature")

    if not (payment_id and order_id and signature):
        return jsonify({"success": False, "error": "Missing payment verification fields."}), 400

    expected_order_id = session.get(f"rzp_order_{project_id}")
    if expected_order_id and expected_order_id != order_id:
        return jsonify({"success": False, "error": "Order mismatch."}), 400

    client = get_razorpay_client()
    if client is None:
        return jsonify({"success": False, "error": "Gateway not configured."}), 500

    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"success": False, "error": "Signature verification failed."}), 400

    project = mark_project_paid(project_id, payment_id)
    if project is None:
        return jsonify({"success": False, "error": "Project not found."}), 404

    session.pop(f"rzp_order_{project_id}", None)

    return jsonify(
        {
            "success": True,
            "redirect": f"/thank-you/{project_id}",
        }
    )


@payment_bp.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    if not config.RAZORPAY_WEBHOOK_SECRET:
        return jsonify({"status": "ignored"}), 200

    received_sig = request.headers.get("X-Razorpay-Signature", "")
    raw_body = request.get_data()

    expected_sig = hmac.new(
        config.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, received_sig):
        return jsonify({"status": "invalid signature"}), 400

    payload = json.loads(raw_body.decode("utf-8"))
    if payload.get("event") in ("payment.captured", "order.paid"):
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment_entity.get("notes", {})
        project_id = notes.get("project_id")
        payment_id = payment_entity.get("id")
        if project_id and payment_id:
            try:
                mark_project_paid(int(project_id), payment_id)
            except ValueError:
                pass

    return jsonify({"status": "ok"}), 200


@payment_bp.route("/create-payment", methods=["POST"])
def create_payment():
    client = get_razorpay_client()
    if client is None:
        return jsonify({"error": "Razorpay keys not configured"}), 500

    try:
        amount = int(request.form.get("price", 0))
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    try:
        razorpay_order = client.order.create(
            {
                "amount": amount * 100,
                "currency": "INR",
                "payment_capture": 1,
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify(razorpay_order)
