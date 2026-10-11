import sqlite3
from pathlib import Path

DB_PATH = Path("data/laya.db")

def get_connection():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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