import os
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
)
from werkzeug.utils import secure_filename

import config
from models.database import get_db_connection

services_bp = Blueprint("services", __name__)

SERVICES = {
    "photo-editing": {
        "title": "Photo Editing",
        "tagline": "Editorial retouching, skin accuracy & cinematic color grading.",
        "description": "High-end retouching, lighting balance, background cleanup, and color grading crafted for creators and brands.",
        "starting_price": 499,
        "packages": {
            "Basic": {
                "price": 499,
                "turnaround": "3 Days",
                "features": ["Clean color correction", "Basic skin & blemish retouch", "1 revision round", "High-res export"],
            },
            "Standard": {
                "price": 999,
                "turnaround": "2 Days",
                "featured": True,
                "features": ["Advanced editorial retouching", "Cinematic color grading", "2 revision rounds", "RAW + social formats"],
            },
            "Premium": {
                "price": 1999,
                "turnaround": "24 Hours",
                "features": ["Full magazine-grade finish", "Lighting & composite polish", "Unlimited revisions", "Priority 24h delivery"],
            },
        },
    },
    "video-editing": {
        "title": "Video Editing",
        "tagline": "Story-driven long-form edits with sound design & motion graphics.",
        "description": "High-retention YouTube, documentary, and brand video editing with pacing, soundscapes, and custom color.",
        "starting_price": 999,
        "packages": {
            "Basic": {
                "price": 999,
                "turnaround": "4 Days",
                "features": ["Clean cuts & pacing", "Basic audio leveling", "Subtle transitions", "1 revision round"],
            },
            "Standard": {
                "price": 2999,
                "turnaround": "3 Days",
                "featured": True,
                "features": ["Cinematic storytelling cut", "Motion graphics & titles", "Full sound design & grading", "2 revision rounds"],
            },
            "Premium": {
                "price": 4999,
                "turnaround": "48 Hours",
                "features": ["Director-level production edit", "4K master + custom LUTs", "Dedicated creative direction", "Priority 48h turnaround"],
            },
        },
    },
    "reels-editing": {
        "title": "Instagram Reels",
        "tagline": "Hook-first vertical edits engineered for reach and retention.",
        "description": "Dynamic vertical videos for Instagram Reels, YouTube Shorts, and TikTok with kinetic captions and SFX.",
        "starting_price": 799,
        "packages": {
            "Basic": {
                "price": 799,
                "turnaround": "48 Hours",
                "features": ["Up to 60s vertical cut", "Clean animated captions", "Beat-synced cuts", "1 revision round"],
            },
            "Standard": {
                "price": 1799,
                "turnaround": "24 Hours",
                "featured": True,
                "features": ["High-retention hook design", "Motion graphics & B-roll", "SFX + color grade", "2 revision rounds"],
            },
            "Premium": {
                "price": 2999,
                "turnaround": "Same / Next Day",
                "features": ["Viral-style 3D/kinetic motion", "Custom sound & visual pacing", "Thumbnail cover frame", "Unlimited revisions"],
            },
        },
    },
    "thumbnail-design": {
        "title": "Thumbnail Design",
        "tagline": "High-CTR visuals built to stop the scroll instantly.",
        "description": "Click-worthy YouTube and campaign thumbnails with expressive compositing, typography, and contrast.",
        "starting_price": 299,
        "packages": {
            "Basic": {
                "price": 299,
                "turnaround": "48 Hours",
                "features": ["1 custom thumbnail", "Subject cutout & color pop", "Bold readable typography", "1 revision round"],
            },
            "Standard": {
                "price": 599,
                "turnaround": "24 Hours",
                "featured": True,
                "features": ["1 high-CTR composite design", "Lighting & glow FX", "A/B text variation", "2 revision rounds"],
            },
            "Premium": {
                "price": 999,
                "turnaround": "12 Hours",
                "features": ["2 A/B test concepts", "Source PSD included", "Express priority delivery", "Unlimited revisions"],
            },
        },
    },
}


def resolve_service_and_price(service_input, package_input):
    """Look up authoritative service title, package name, and price server-side."""
    if not service_input:
        return None, None, None

    normalized = service_input.strip().lower()
    matched_service = None

    for slug, svc in SERVICES.items():
        if normalized == slug or normalized == svc["title"].lower():
            matched_service = svc
            break

    if not matched_service:
        return None, None, None

    pkg_clean = (package_input or "Standard").strip().lower()
    for pkg_name, pkg_data in matched_service["packages"].items():
        if pkg_clean == pkg_name.lower():
            return matched_service["title"], pkg_name, pkg_data["price"]

    std = matched_service["packages"]["Standard"]
    return matched_service["title"], "Standard", std["price"]


@services_bp.route("/")
def home():
    return render_template("home.html", services=SERVICES)


@services_bp.route("/services")
def services():
    return render_template("services.html", services=SERVICES)


@services_bp.route("/services/thumbnails")
def thumbnails_alias():
    return redirect("/services/thumbnail-design")


@services_bp.route("/services/<service_slug>")
def service_detail(service_slug):
    service = SERVICES.get(service_slug)
    if service is None:
        return render_template("services.html", services=SERVICES), 404

    return render_template(
        "service_detail.html",
        service=service,
        service_slug=service_slug,
    )


@services_bp.route("/start-project", methods=["GET", "POST"])
def start_project():
    if request.method == "GET":
        raw_service = request.args.get("service", "")
        raw_package = request.args.get("package", "")
        resolved_service, resolved_package, resolved_price = resolve_service_and_price(
            raw_service, raw_package
        )

        if not resolved_service:
            resolved_service = "Video Editing"
            resolved_package = "Standard"
            resolved_price = SERVICES["video-editing"]["packages"]["Standard"]["price"]

        return render_template(
            "start_project.html",
            services=SERVICES,
            service=resolved_service,
            package=resolved_package,
            price=resolved_price,
        )

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    project_type = request.form.get("project_type", "").strip()
    description = request.form.get("description", "").strip()
    raw_service = request.form.get("service", "").strip()
    raw_package = request.form.get("package", "").strip()

    service, package, price = resolve_service_and_price(raw_service, raw_package)

    if not name or not email or not description:
        flash("Please complete all required project fields.", "error")
        return redirect("/start-project")

    if not service or not price:
        flash("Please select a valid service and package.", "error")
        return redirect("/start-project")

    if not project_type:
        project_type = service

    filename = None
    uploaded_file = request.files.get("project_file")
    if uploaded_file and uploaded_file.filename:
        safe_name = secure_filename(uploaded_file.filename)
        if safe_name:
            os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
            filename = f"{int(datetime.now().timestamp())}_{safe_name}"
            uploaded_file.save(os.path.join(config.UPLOAD_FOLDER, filename))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = session.get("user_id")

    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO projects(
            name, email, project_type, description, filename,
            service_name, package_name, price, payment_status,
            user_id, created_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
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
            user_id,
            now_str,
        ),
    )
    project_id = cursor.lastrowid

    if user_id:
        conn.execute(
            """
            INSERT INTO notifications(
                user_id, project_id, title, description, is_read, created_at
            )
            VALUES(?,?,?,?,?,?)
            """,
            (
                user_id,
                project_id,
                "Project Submitted",
                f"Your {service} ({package}) project has been submitted. Complete payment to begin editing.",
                0,
                now_str,
            ),
        )

    conn.commit()
    conn.close()

    config.notify_owner(
        f"New Project Request #{project_id} — {service} (₹{price})",
        f"""
        <div style="font-family:Inter,Arial,sans-serif;padding:24px;background:#0b0d15;color:#eef2ff;border-radius:12px;">
            <h2 style="margin-top:0;">New Project Submitted (#{project_id})</h2>
            <p><strong>Client:</strong> {name} ({email})</p>
            <p><strong>Service:</strong> {service} — {package}</p>
            <p><strong>Amount:</strong> ₹{price} (Payment Pending)</p>
            <p><strong>Project Type:</strong> {project_type}</p>
            <p><strong>Brief:</strong><br>{description}</p>
            <p><strong>Uploaded File:</strong> {filename or 'None'}</p>
        </div>
        """,
        f"New project #{project_id} from {name} ({email}) for {service} - {package} (₹{price}).",
    )

    return redirect(f"/pay/{project_id}")


@services_bp.route("/thank-you/<int:project_id>")
def thank_you(project_id):
    conn = get_db_connection()
    project = conn.execute(
        "SELECT * FROM projects WHERE id=?",
        (project_id,),
    ).fetchone()
    conn.close()

    if project is None:
        return "Project not found", 404

    return render_template("thank_you.html", project=project)


@services_bp.route("/track-project", methods=["GET", "POST"])
def track_project():
    projects = None
    searched_email = ""
    if request.method == "POST":
        searched_email = request.form.get("email", "").strip().lower()
        if searched_email:
            conn = get_db_connection()
            projects = conn.execute(
                """
                SELECT * FROM projects
                WHERE LOWER(email)=?
                ORDER BY created_at DESC
                """,
                (searched_email,),
            ).fetchall()
            conn.close()

    return render_template(
        "track_project.html",
        projects=projects,
        searched_email=searched_email,
    )


@services_bp.route("/terms")
def terms_page():
    return render_template(
        "legal.html",
        page_title="Terms & Conditions",
        page_body=f"""
        <p>Welcome to <strong>{config.STUDIO_NAME}</strong>. By placing an order on this website, you agree to provide accurate project briefs and rights-cleared raw media files.</p>
        <p><strong>Deliverables & Turnaround:</strong> Estimated delivery timelines (12 hours to 4 days depending on the selected package) begin after payment confirmation and receipt of all required raw files.</p>
        <p><strong>Revisions:</strong> Each package includes the stated number of revision rounds covering reasonable creative adjustments within the original project scope.</p>
        <p><strong>Payments:</strong> All payments are processed securely in INR via Razorpay.</p>
        """,
    )


@services_bp.route("/privacy")
def privacy_page():
    return render_template(
        "legal.html",
        page_title="Privacy Policy",
        page_body=f"""
        <p><strong>{config.STUDIO_NAME}</strong> respects your privacy and confidentiality.</p>
        <p><strong>Information Collected:</strong> We collect your name, email address, project brief, and uploaded creative assets solely to fulfill your editing order and communicate progress updates.</p>
        <p><strong>Payment Security:</strong> Card, UPI, and banking credentials are handled directly by Razorpay and are never stored on our servers.</p>
        <p><strong>Confidentiality:</strong> Client footage, photos, and project files are never shared publicly or with third parties without explicit permission.</p>
        """,
    )


@services_bp.route("/refund-policy")
def refund_page():
    email = config.OWNER_EMAIL or "contact@vikasstudio.com"
    return render_template(
        "legal.html",
        page_title="Cancellation & Refund Policy",
        page_body=f"""
        <p><strong>Before Editing Starts:</strong> If you cancel an order before our studio begins reviewing or editing your files (typically within 6 hours of payment), you are eligible for a full refund.</p>
        <p><strong>Once Work Has Started:</strong> Because creative editing is a custom service, orders already in <em>Editing</em> or <em>Delivered</em> status are non-refundable, though we will fulfill all included revisions to ensure quality.</p>
        <p><strong>Refund Processing Time:</strong> Approved refunds are initiated within 2 business days and credited to your original payment method within 5–7 business days via Razorpay.</p>
        <p>For refund requests, email <a href="mailto:{email}" style="color:#00d4ff;">{email}</a> with your Project ID.</p>
        """,
    )


@services_bp.route("/contact")
def contact_page():
    email = config.OWNER_EMAIL or "contact@vikasstudio.com"
    return render_template(
        "legal.html",
        page_title="Contact & About Us",
        page_body=f"""
        <p><strong>{config.STUDIO_NAME}</strong> is an India-based creative post-production studio specializing in Video Editing, Photo Retouching, Instagram Reels, and YouTube Thumbnail Design.</p>
        <p><strong>Support Email:</strong> <a href="mailto:{email}" style="color:#00d4ff;">{email}</a></p>
        <p><strong>Business Hours:</strong> Monday – Saturday, 10:00 AM – 7:00 PM IST</p>
        <p><strong>Order Tracking:</strong> Existing clients can track real-time order progress via their <a href="/dashboard" style="color:#00d4ff;">Dashboard</a> or <a href="/track-project" style="color:#00d4ff;">Track Order</a> page.</p>
        """,
    )
