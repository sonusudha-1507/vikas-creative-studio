import sqlite3


conn = sqlite3.connect(
    "database/projects.db"
)


cursor = conn.cursor()


try:

    cursor.execute(
        """
        ALTER TABLE projects
        ADD COLUMN user_id INTEGER
        """
    )


    print(
        "user_id added successfully"
    )


except Exception as e:

    print(e)


conn.commit()

conn.close()
