import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE = os.path.join(BASE_DIR, "database", "projects.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

DELIVERY_FOLDER = os.path.join(BASE_DIR, "deliveries")

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "vikas-secret-key"
)

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")

RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
