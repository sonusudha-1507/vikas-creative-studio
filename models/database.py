import sqlite3

DB_PATH = os.getenv(
    "DB_PATH",
    "database/projects.db"
)

def get_db_connection():
    print("Using database:", DB_PATH)

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


def init_database():

    conn = get_db_connection()

    cursor = conn.cursor()

    # -------------------------------------------------
    # USERS
    # -------------------------------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        email TEXT UNIQUE,

        password TEXT,

        created_at TEXT

    )

    """)

    # -------------------------------------------------
    # PROJECTS
    # -------------------------------------------------

    cursor.execute("""

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

        payment_status TEXT DEFAULT 'Pending',

        payment_id TEXT,

        user_id INTEGER,

        delivery_file TEXT,

        status TEXT DEFAULT 'Submitted',

        created_at TEXT

    )

    """)

    # -------------------------------------------------
    # PAYMENTS
    # -------------------------------------------------

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

    # -------------------------------------------------
    # CHAT
    # -------------------------------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS messages(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        project_id INTEGER,

        sender TEXT,

        message TEXT,

        is_read INTEGER DEFAULT 0,

        created_at TEXT

    )

    """)

    cursor.execute("""

    CREATE INDEX IF NOT EXISTS idx_messages_project

    ON messages(project_id)

    """)

    # -------------------------------------------------
    # NOTIFICATIONS
    # -------------------------------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS notifications(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        project_id INTEGER,

        title TEXT,

        description TEXT,

        is_read INTEGER DEFAULT 0,

        created_at TEXT

    )

    """)

    cursor.execute("""

    CREATE INDEX IF NOT EXISTS idx_notifications_user

    ON notifications(user_id)

    """)

    conn.commit()

    conn.close()