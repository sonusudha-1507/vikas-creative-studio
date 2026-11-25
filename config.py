import os
import smtplib
import threading
import requests
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.getenv("DB_PATH", os.path.join(BASE_DIR, "database", "projects.db"))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DELIVERY_FOLDER = os.path.join(BASE_DIR, "deliveries")

SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(24).hex()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "vikas")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# Email & Owner Notification Settings
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")
STUDIO_NAME = os.getenv("STUDIO_NAME", "VIKAS Creative Studio")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USER
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")


def _send_email_worker(to_email, subject, html_body, text_body):
    if not to_email:
        return

    # Option 1: Resend HTTP API (recommended on cloud hosts like Render)
    if RESEND_API_KEY and SMTP_FROM:
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{STUDIO_NAME} <{SMTP_FROM}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body or subject,
                },
                timeout=15,
            )
            if resp.status_code >= 400:
                print("Resend email error:", resp.status_code, resp.text)
            return
        except Exception as exc:
            print("Resend request failed:", exc)

    # Option 2: Standard SMTP (Gmail App Password, Zoho, Brevo, etc.)
    if not (SMTP_USER and SMTP_PASSWORD):
        print(f"[Email skipped - SMTP/Resend not configured] To: {to_email} | Subject: {subject}")
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{STUDIO_NAME} <{SMTP_FROM or SMTP_USER}>"
        msg["To"] = to_email
        msg.set_content(text_body or subject)
        msg.add_alternative(html_body, subtype="html")

        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
    except Exception as exc:
        print("SMTP email failed:", exc)


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
