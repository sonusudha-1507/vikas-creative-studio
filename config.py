import os
import smtplib
import threading
import requests
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.getenv("DB_PATH") or os.path.join(BASE_DIR, "database", "projects.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DELIVERY_FOLDER = os.path.join(BASE_DIR, "deliveries")

SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(24).hex()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "vikas")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Email & Owner Notification Settings
OWNER_EMAIL = (os.getenv("OWNER_EMAIL") or "").strip()
STUDIO_NAME = os.getenv("STUDIO_NAME") or "VIKAS Creative Studio"

BREVO_API_KEY = (os.getenv("BREVO_API_KEY") or "").strip()
RESEND_API_KEY = (os.getenv("RESEND_API_KEY") or "").strip()

SMTP_HOST = os.getenv("SMTP_HOST") or "smtp.gmail.com"
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER = (os.getenv("SMTP_USER") or "").strip()
SMTP_PASSWORD = (os.getenv("SMTP_PASSWORD") or "").strip()
SMTP_FROM = (os.getenv("SMTP_FROM") or SMTP_USER or OWNER_EMAIL).strip()


def send_email_sync(to_email, subject, html_body, text_body=None):
    """Send email synchronously and return (success: bool, message: str)."""
    if not to_email:
        return False, "Recipient email is empty."

    sender_email = SMTP_FROM or OWNER_EMAIL

    # Option 1: Brevo HTTP API over HTTPS Port 443 (works on Render Free with Gmail)
    if BREVO_API_KEY:
        if not sender_email:
            return False, "Set SMTP_FROM or OWNER_EMAIL to your verified Brevo sender email."
        try:
            resp = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": BREVO_API_KEY,
                    "content-type": "application/json",
                },
                json={
                    "sender": {"name": STUDIO_NAME, "email": sender_email},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "htmlContent": html_body,
                    "textContent": text_body or subject,
                },
                timeout=15,
            )
            if resp.status_code < 300:
                return True, f"Sent via Brevo to {to_email}"
            return False, f"Brevo error ({resp.status_code}): {resp.text}"
        except Exception as exc:
            return False, f"Brevo request failed: {exc}"

    # Option 2: Resend HTTP API over HTTPS Port 443
    if RESEND_API_KEY:
        if not sender_email:
            return False, "Set SMTP_FROM to your verified Resend sender email."
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{STUDIO_NAME} <{sender_email}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body or subject,
                },
                timeout=15,
            )
            if resp.status_code < 300:
                return True, f"Sent via Resend to {to_email}"
            return False, f"Resend error ({resp.status_code}): {resp.text}"
        except Exception as exc:
            return False, f"Resend request failed: {exc}"

    # Option 3: Standard SMTP (works locally / PythonAnywhere; blocked on Render Free)
    if not (SMTP_USER and SMTP_PASSWORD):
        return False, "No email provider configured (set BREVO_API_KEY, RESEND_API_KEY, or SMTP credentials)."

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{STUDIO_NAME} <{sender_email or SMTP_USER}>"
        msg["To"] = to_email
        msg.set_content(text_body or subject)
        msg.add_alternative(html_body, subtype="html")

        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=12) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        return True, f"Sent via SMTP to {to_email}"
    except Exception as exc:
        return False, f"SMTP failed: {exc}"


def _send_email_worker(to_email, subject, html_body, text_body):
    ok, info = send_email_sync(to_email, subject, html_body, text_body)
    if not ok:
        print("[Email Error]", info)


def send_email_async(to_email, subject, html_body, text_body=None):
    if not to_email:
        return
    thread = threading.Thread(
        target=_send_email_worker,
        args=(to_email, subject, html_body, text_body),
        daemon=True,
    )
    thread.start()


def notify_owner(subject, html_body, text_body=None):
    if OWNER_EMAIL:
        send_email_async(OWNER_EMAIL, subject, html_body, text_body)


def notify_client(client_email, subject, html_body, text_body=None):
    if client_email:
        send_email_async(client_email, subject, html_body, text_body)
