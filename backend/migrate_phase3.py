import sqlite3


connection = sqlite3.connect("notes.db")
try:
    columns = {row[1] for row in connection.execute("PRAGMA table_info(notes)")}
    if "summary" not in columns:
        connection.execute("ALTER TABLE notes ADD COLUMN summary TEXT")
        print("Added summary column.")
    if "key_points" not in columns:
        connection.execute("ALTER TABLE notes ADD COLUMN key_points TEXT")
        print("Added key_points column.")
    connection.commit()
finally:
    connection.close()

print("Phase 3 database migration complete.")
