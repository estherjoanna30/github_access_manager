import sqlite3

# Connect to DB (creates if not exists)
conn = sqlite3.connect("access_manager.db")
cur = conn.cursor()

# Table: email_mapping
cur.execute("""
CREATE TABLE IF NOT EXISTS email_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL
);
""")

# Table: logs
cur.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    repo TEXT,
    username TEXT,
    permission TEXT,
    status TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
conn.close()

print("✅ Database initialized with tables: email_mapping, logs")
