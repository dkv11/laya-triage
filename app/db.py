import sqlite3
from pathlib import Path

DB_PATH = Path("data/laya.db")

def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Create tables if they don't exist yet. Safe to run many times."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                vibration_mm_s REAL,
                bearing_temp_c REAL,
                current_r_a REAL,
                current_y_a REAL,
                current_b_a REAL,
                flow_m3h REAL,
                pressure_bar REAL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_readings_asset_time "
            "ON readings (asset_id, timestamp)"
        )

        conn.execute("""
            CREATE TABLE IF NOT EXISTS operator_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                asset_id TEXT,
                operator_name TEXT,
                text TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL REFERENCES operator_messages(id),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                asset_id TEXT,
                sensor_snapshot TEXT,
                team TEXT CHECK (team IN ('mechanical', 'electrical', 'instrumentation', 'unknown')),
                issue_type TEXT CHECK (issue_type IN ('routine', 'corrective', 'emergency')),
                priority INTEGER CHECK (priority BETWEEN 1 AND 5),
                reason TEXT,
                first_checks TEXT,
                model TEXT NOT NULL,
                raw_output TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL UNIQUE REFERENCES decisions(id),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_correct INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
                correct_team TEXT,
                correct_issue_type TEXT,
                correct_priority INTEGER,
                comment TEXT,
                corrected_by TEXT
            )
        """)
