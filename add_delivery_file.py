import sqlite3


conn = sqlite3.connect(
    "database/projects.db"
)

cursor = conn.cursor()


try:

    cursor.execute(
        """
        ALTER TABLE projects
        ADD COLUMN delivery_file TEXT
        """
    )


    print(
    "delivery column added"
    )


except Exception as e:

    print(e)


conn.commit()

conn.close()
