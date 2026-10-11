import sqlite3

from app.db import get_connection

conn = get_connection()

# 1. List all tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
print("Tables:", [t["name"] for t in tables])

# 2. Test the guard rail: an invalid team must be rejected
try:
    conn.execute("INSERT INTO operator_messages (text) VALUES ('test')")
    conn.execute("INSERT INTO decisions (message_id, team, model) VALUES (last_insert_rowid(), 'plumber', 'test')")
    print("Problem: invalid team was accepted")
except sqlite3.IntegrityError as e:
    print("Guard rail works:", e)
finally:
    conn.rollback()   # undo the test inserts, keep the database clean
