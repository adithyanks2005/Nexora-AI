from __future__ import annotations

import sqlite3
import os
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(tempfile.gettempdir()) / "nexora-data" if os.getenv("VERCEL") else BASE_DIR / "data"
DB_PATH  = DATA_DIR / "nexora.db"


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
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
