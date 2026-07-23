from __future__ import annotations

import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import get_supabase_server_key, get_supabase_url

BASE_DIR = Path(__file__).resolve().parents[1]

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(BASE_DIR / ".env", override=False)

SUPABASE_URL = get_supabase_url()
SUPABASE_KEY = get_supabase_server_key()
DEFAULT_WORKPLACE_ID = os.getenv("DEFAULT_WORKPLACE_ID", "default").strip() or "default"
USING_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

_supabase_client: Any | None = None


def normalize_workplace_id(workplace_id: str | None = None) -> str:
    return (workplace_id or DEFAULT_WORKPLACE_ID).strip() or DEFAULT_WORKPLACE_ID


def get_supabase() -> Any:
    global _supabase_client
    if not USING_SUPABASE:
        raise RuntimeError("Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    if _supabase_client is None:
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RuntimeError("Install the Supabase client with `pip install supabase`.") from exc
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def _data(result: Any) -> Any:
    return getattr(result, "data", None)


def _one(result: Any) -> dict[str, Any] | None:
    data = _data(result)
    if isinstance(data, list):
        return _normalize_row(data[0]) if data else None
    return _normalize_row(data) if data else None


def _many(result: Any) -> list[dict[str, Any]]:
    data = _data(result) or []
    return [_normalize_row(row) for row in data]


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    if "done" in row:
        row["done"] = int(bool(row["done"]))
    return row


def is_vercel() -> bool:
    return any(os.getenv(k) for k in ["VERCEL", "VERCEL_ENV", "NOW_REGION", "AWS_LAMBDA_FUNCTION_NAME"])


def get_data_dir() -> Path:
    if is_vercel():
        return Path(tempfile.gettempdir()) / "nexora-data"

    local_data = BASE_DIR / "data"
    try:
        local_data.mkdir(parents=True, exist_ok=True)
        test_file = local_data / f".write_test_{os.getpid()}"
        test_file.touch()
        test_file.unlink()
        return local_data
    except Exception:
        return Path(tempfile.gettempdir()) / "nexora-data"


DATA_DIR = get_data_dir()
DB_PATH = DATA_DIR / "nexora.db"


def get_connection() -> sqlite3.Connection:
    if USING_SUPABASE:
        raise RuntimeError("SQLite connection requested while Supabase is configured.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if USING_SUPABASE:
        return

    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                workplace_id  TEXT NOT NULL DEFAULT 'default',
                email         TEXT NOT NULL,
                name          TEXT NOT NULL DEFAULT '',
                picture       TEXT NOT NULL DEFAULT '',
                created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(email, workplace_id)
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id            TEXT PRIMARY KEY,
                workplace_id  TEXT NOT NULL DEFAULT 'default',
                user_id       TEXT NOT NULL DEFAULT '',
                title         TEXT NOT NULL DEFAULT 'New Chat',
                created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                workplace_id  TEXT NOT NULL DEFAULT 'default',
                session_id    TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                role          TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content       TEXT NOT NULL,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                workplace_id  TEXT NOT NULL DEFAULT 'default',
                user_id       TEXT NOT NULL DEFAULT '',
                title         TEXT NOT NULL,
                time          TEXT NOT NULL,
                repeat        TEXT NOT NULL DEFAULT 'Daily',
                notes         TEXT DEFAULT '',
                icon          TEXT DEFAULT '💊',
                color         TEXT DEFAULT '#E6F1FB',
                done          INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS health_records (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                workplace_id  TEXT NOT NULL DEFAULT 'default',
                user_id       TEXT NOT NULL DEFAULT '',
                type          TEXT NOT NULL,
                data          TEXT NOT NULL,
                notes         TEXT DEFAULT '',
                recorded_at   TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)

        migrations = {
            "users": ["workplace_id TEXT NOT NULL DEFAULT 'default'"],
            "chat_sessions": [
                "user_id TEXT NOT NULL DEFAULT ''",
                "workplace_id TEXT NOT NULL DEFAULT 'default'",
            ],
            "chat_messages": ["workplace_id TEXT NOT NULL DEFAULT 'default'"],
            "reminders": [
                "user_id TEXT NOT NULL DEFAULT ''",
                "workplace_id TEXT NOT NULL DEFAULT 'default'",
            ],
            "health_records": [
                "user_id TEXT NOT NULL DEFAULT ''",
                "workplace_id TEXT NOT NULL DEFAULT 'default'",
            ],
        }
        for table, columns in migrations.items():
            for column in columns:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column}")
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc).lower():
                        print(f"Migration warning for {table}: {exc}")


def get_user(user_id: str, workplace_id: str | None = None) -> dict[str, Any] | None:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        return _one(
            get_supabase()
            .table("users")
            .select("*")
            .eq("id", user_id)
            .eq("workplace_id", workplace_id)
            .limit(1)
            .execute()
        )

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ? AND workplace_id = ?",
            (user_id, workplace_id),
        ).fetchone()
    return _normalize_row(dict(row)) if row else None


def upsert_user(email: str, name: str, picture: str, workplace_id: str | None = None) -> dict[str, Any]:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        client = get_supabase()
        existing = _one(
            client.table("users")
            .select("*")
            .eq("email", email)
            .eq("workplace_id", workplace_id)
            .limit(1)
            .execute()
        )
        if existing:
            updated = _one(
                client.table("users")
                .update({"name": name, "picture": picture})
                .eq("id", existing["id"])
                .eq("workplace_id", workplace_id)
                .execute()
            )
            return updated or {**existing, "name": name, "picture": picture}

        user = {
            "id": str(uuid.uuid4()),
            "workplace_id": workplace_id,
            "email": email,
            "name": name,
            "picture": picture,
        }
        return _one(client.table("users").insert(user).execute()) or user

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? AND workplace_id = ?",
            (email, workplace_id),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET name = ?, picture = ? WHERE id = ? AND workplace_id = ?",
                (name, picture, row["id"], workplace_id),
            )
            refreshed = conn.execute("SELECT * FROM users WHERE id = ?", (row["id"],)).fetchone()
            return dict(refreshed)

        user_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users (id, workplace_id, email, name, picture) VALUES (?, ?, ?, ?, ?)",
            (user_id, workplace_id, email, name, picture),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row)


def create_user(user: dict[str, Any]) -> dict[str, Any]:
    user = {**user, "workplace_id": normalize_workplace_id(user.get("workplace_id"))}
    if USING_SUPABASE:
        return _one(get_supabase().table("users").insert(user).execute()) or user

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (id, workplace_id, email, name, picture) VALUES (?, ?, ?, ?, ?)",
            (user["id"], user["workplace_id"], user["email"], user.get("name", ""), user.get("picture", "")),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return dict(row)


def list_chat_sessions(user_id: str, workplace_id: str) -> list[dict[str, Any]]:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        return _many(
            get_supabase()
            .table("chat_sessions")
            .select("*")
            .eq("user_id", user_id)
            .eq("workplace_id", workplace_id)
            .order("updated_at", desc=True)
            .execute()
        )

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_sessions WHERE user_id = ? AND workplace_id = ? ORDER BY updated_at DESC",
            (user_id, workplace_id),
        ).fetchall()
    return [dict(r) for r in rows]


def get_chat_session(session_id: str, user_id: str, workplace_id: str) -> dict[str, Any] | None:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        return _one(
            get_supabase()
            .table("chat_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("user_id", user_id)
            .eq("workplace_id", workplace_id)
            .limit(1)
            .execute()
        )

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ? AND workplace_id = ?",
            (session_id, user_id, workplace_id),
        ).fetchone()
    return dict(row) if row else None


def get_chat_session_by_id(session_id: str) -> dict[str, Any] | None:
    if USING_SUPABASE:
        return _one(
            get_supabase()
            .table("chat_sessions")
            .select("*")
            .eq("id", session_id)
            .limit(1)
            .execute()
        )

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    return dict(row) if row else None


def create_chat_session(session_id: str, user_id: str, workplace_id: str, title: str) -> dict[str, Any]:
    workplace_id = normalize_workplace_id(workplace_id)
    row = {"id": session_id, "user_id": user_id, "workplace_id": workplace_id, "title": title}
    if USING_SUPABASE:
        return _one(get_supabase().table("chat_sessions").insert(row).execute()) or row

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, user_id, workplace_id, title) VALUES (?, ?, ?, ?)",
            (session_id, user_id, workplace_id, title),
        )
        found = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    return dict(found)


def delete_chat_session(session_id: str, user_id: str, workplace_id: str) -> None:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        get_supabase().table("chat_sessions").delete().eq("id", session_id).eq("user_id", user_id).eq(
            "workplace_id", workplace_id
        ).execute()
        return

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM chat_sessions WHERE id = ? AND user_id = ? AND workplace_id = ?",
            (session_id, user_id, workplace_id),
        )


def list_chat_messages(session_id: str, workplace_id: str) -> list[dict[str, Any]]:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        return _many(
            get_supabase()
            .table("chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .eq("workplace_id", workplace_id)
            .order("created_at")
            .execute()
        )

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? AND workplace_id = ? ORDER BY created_at",
            (session_id, workplace_id),
        ).fetchall()
    return [dict(r) for r in rows]


def add_chat_message(session_id: str, workplace_id: str, role: str, content: str) -> dict[str, Any]:
    workplace_id = normalize_workplace_id(workplace_id)
    row = {"session_id": session_id, "workplace_id": workplace_id, "role": role, "content": content}
    if USING_SUPABASE:
        return _one(get_supabase().table("chat_messages").insert(row).execute()) or row

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO chat_messages (session_id, workplace_id, role, content) VALUES (?, ?, ?, ?)",
            (session_id, workplace_id, role, content),
        )
        found = conn.execute("SELECT * FROM chat_messages WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(found)


def touch_chat_session(session_id: str, user_id: str, workplace_id: str, title: str | None = None) -> None:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        payload: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if title:
            session = get_chat_session(session_id, user_id, workplace_id)
            if session and session.get("title") == "New Chat":
                payload["title"] = title
        get_supabase().table("chat_sessions").update(payload).eq("id", session_id).eq("user_id", user_id).eq(
            "workplace_id", workplace_id
        ).execute()
        return

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE chat_sessions
            SET updated_at = datetime('now'),
                title = CASE WHEN title = 'New Chat' THEN ? ELSE title END
            WHERE id = ? AND user_id = ? AND workplace_id = ?
            """,
            (title or "Chat", session_id, user_id, workplace_id),
        )


def list_reminders(user_id: str, workplace_id: str) -> list[dict[str, Any]]:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        return _many(
            get_supabase()
            .table("reminders")
            .select("*")
            .eq("user_id", user_id)
            .eq("workplace_id", workplace_id)
            .order("created_at", desc=True)
            .execute()
        )

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM reminders WHERE user_id = ? AND workplace_id = ? ORDER BY created_at DESC",
            (user_id, workplace_id),
        ).fetchall()
    return [_normalize_row(dict(r)) for r in rows]


def create_reminder(user_id: str, workplace_id: str, data: dict[str, Any]) -> dict[str, Any]:
    workplace_id = normalize_workplace_id(workplace_id)
    row = {**data, "user_id": user_id, "workplace_id": workplace_id}
    if USING_SUPABASE:
        return _one(get_supabase().table("reminders").insert(row).execute()) or row

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO reminders (user_id, workplace_id, title, time, repeat, notes, icon, color)
            VALUES (:user_id, :workplace_id, :title, :time, :repeat, :notes, :icon, :color)
            """,
            row,
        )
        found = conn.execute("SELECT * FROM reminders WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _normalize_row(dict(found))


def toggle_reminder_done(reminder_id: int, user_id: str, workplace_id: str) -> dict[str, Any] | None:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        client = get_supabase()
        existing = _one(
            client.table("reminders")
            .select("*")
            .eq("id", reminder_id)
            .eq("user_id", user_id)
            .eq("workplace_id", workplace_id)
            .limit(1)
            .execute()
        )
        if not existing:
            return None
        return _one(
            client.table("reminders")
            .update({"done": not bool(existing.get("done"))})
            .eq("id", reminder_id)
            .eq("user_id", user_id)
            .eq("workplace_id", workplace_id)
            .execute()
        )

    with get_connection() as conn:
        conn.execute(
            "UPDATE reminders SET done = CASE WHEN done = 1 THEN 0 ELSE 1 END WHERE id = ? AND user_id = ? AND workplace_id = ?",
            (reminder_id, user_id, workplace_id),
        )
        row = conn.execute(
            "SELECT * FROM reminders WHERE id = ? AND user_id = ? AND workplace_id = ?",
            (reminder_id, user_id, workplace_id),
        ).fetchone()
    return _normalize_row(dict(row)) if row else None


def delete_reminder(reminder_id: int, user_id: str, workplace_id: str) -> None:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        get_supabase().table("reminders").delete().eq("id", reminder_id).eq("user_id", user_id).eq(
            "workplace_id", workplace_id
        ).execute()
        return

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM reminders WHERE id = ? AND user_id = ? AND workplace_id = ?",
            (reminder_id, user_id, workplace_id),
        )


def clear_done_reminders(user_id: str, workplace_id: str) -> None:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        get_supabase().table("reminders").delete().eq("done", True).eq("user_id", user_id).eq(
            "workplace_id", workplace_id
        ).execute()
        return

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM reminders WHERE done = 1 AND user_id = ? AND workplace_id = ?",
            (user_id, workplace_id),
        )


def list_health_records(user_id: str, workplace_id: str) -> list[dict[str, Any]]:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        return _many(
            get_supabase()
            .table("health_records")
            .select("*")
            .eq("user_id", user_id)
            .eq("workplace_id", workplace_id)
            .order("recorded_at", desc=True)
            .limit(100)
            .execute()
        )

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM health_records WHERE user_id = ? AND workplace_id = ? ORDER BY recorded_at DESC LIMIT 100",
            (user_id, workplace_id),
        ).fetchall()
    return [dict(r) for r in rows]


def create_health_record(user_id: str, workplace_id: str, data: dict[str, Any]) -> dict[str, Any]:
    workplace_id = normalize_workplace_id(workplace_id)
    row = {**data, "user_id": user_id, "workplace_id": workplace_id}
    if USING_SUPABASE:
        return _one(get_supabase().table("health_records").insert(row).execute()) or row

    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO health_records (user_id, workplace_id, type, data, notes) VALUES (:user_id, :workplace_id, :type, :data, :notes)",
            row,
        )
        found = conn.execute("SELECT * FROM health_records WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(found)


def delete_health_record(record_id: int, user_id: str, workplace_id: str) -> None:
    workplace_id = normalize_workplace_id(workplace_id)
    if USING_SUPABASE:
        get_supabase().table("health_records").delete().eq("id", record_id).eq("user_id", user_id).eq(
            "workplace_id", workplace_id
        ).execute()
        return

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM health_records WHERE id = ? AND user_id = ? AND workplace_id = ?",
            (record_id, user_id, workplace_id),
        )
