from __future__ import annotations

import sqlite3
import os
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

def is_vercel() -> bool:
    """Check if we are running in a Vercel environment."""
    return any(os.getenv(k) for k in ["VERCEL", "VERCEL_ENV", "NOW_REGION", "AWS_LAMBDA_FUNCTION_NAME"])

def get_data_dir() -> Path:
    """Determine the best directory for storing data, falling back to /tmp if needed."""
    # Priority 1: Use /tmp on Vercel
    if is_vercel():
        tmp_dir = Path(tempfile.gettempdir()) / "nexora-data"
        print(f"DEBUG: Vercel environment detected. Using {tmp_dir}")
        return tmp_dir
    
    # Priority 2: Use local 'data' directory if writable
    local_data = BASE_DIR / "data"
    print(f"DEBUG: Checking local data directory: {local_data}")
    try:
        local_data.mkdir(parents=True, exist_ok=True)
        # Test writability
        test_file = local_data / f".write_test_{os.getpid()}"
        test_file.touch()
        test_file.unlink()
        print(f"DEBUG: Local data directory is writable: {local_data}")
        return local_data
    except Exception as e:
        # Priority 3: Fallback to /tmp if local is read-only
        tmp_dir = Path(tempfile.gettempdir()) / "nexora-data"
        print(f"DEBUG: Local data directory is NOT writable ({e}). Falling back to {tmp_dir}")
        return tmp_dir

DATA_DIR = get_data_dir()
DB_PATH  = DATA_DIR / "nexora.db"


def get_connection() -> sqlite3.Connection:
    if not DATA_DIR.exists():
        try:
            print(f"Creating data directory at: {DATA_DIR}")
            DATA_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Final fallback if even get_data_dir's choice fails
            print(f"Failed to create {DATA_DIR}: {e}. Falling back to system temp.")
            fallback = Path(tempfile.gettempdir()) / "nexora-fallback"
            fallback.mkdir(parents=True, exist_ok=True)
            return sqlite3.connect(fallback / "nexora.db")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL DEFAULT 'New Chat',
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                role        TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content     TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                time        TEXT NOT NULL,
                repeat      TEXT NOT NULL DEFAULT 'Daily',
                notes       TEXT DEFAULT '',
                icon        TEXT DEFAULT '💊',
                color       TEXT DEFAULT '#E6F1FB',
                done        INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS health_records (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                type        TEXT NOT NULL,
                data        TEXT NOT NULL,
                notes       TEXT DEFAULT '',
                recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        # seed default reminders if empty
        count = conn.execute("SELECT COUNT(*) FROM reminders").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO reminders (title,time,repeat,notes,icon,color) VALUES (?,?,?,?,?,?)",
                [
                    ("Morning vitamins",  "08:00", "Daily", "With breakfast", "💊", "#E6F1FB"),
                    ("Drink water",       "10:00", "Daily", "500 ml",         "💧", "#E1F5EE"),
                    ("Evening walk",      "18:30", "Daily", "30 minutes",     "🏃", "#FAEEDA"),
                ],
            )
