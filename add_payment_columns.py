import sqlite3


conn = sqlite3.connect(
    "database/projects.db"
)


cursor = conn.cursor()


columns = [

    ("payment_status", "TEXT DEFAULT 'Pending'"),

    ("payment_id", "TEXT")

]


for column, datatype in columns:


    try:


        cursor.execute(

            f"""
            ALTER TABLE projects
            ADD COLUMN {column} {datatype}
            """

        )


        print(
            column,
            "added"
        )


    except Exception as e:


        print(
            column,
            e
        )


conn.commit()

conn.close()
