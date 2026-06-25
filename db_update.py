import sqlite3

conn = sqlite3.connect("database/projects.db")
cursor = conn.cursor()

# Add columns safely (ignore if already exists)
try:
    cursor.execute("ALTER TABLE projects ADD COLUMN service_name TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE projects ADD COLUMN package_name TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE projects ADD COLUMN price INTEGER")
except:
    pass

conn.commit()
conn.close()

print("Database updated successfully")
