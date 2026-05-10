from __future__ import annotations

import uuid
from typing import Any

from backend.database import get_connection


def create_session(title: str = "New Chat") -> dict[str, Any]:
    sid = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, title) VALUES (?, ?)", (sid, title)
        )
        row = conn.execute(
            "SELECT * FROM chat_sessions WHERE id = ?", (sid,)
        ).fetchone()
    return dict(row)


def list_sessions() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_sessions ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_session(sid: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM chat_sessions WHERE id = ?", (sid,)
        ).fetchone()
    return dict(row) if row else None


def rename_session(sid: str, title: str) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, sid),
        )
        row = conn.execute(
            "SELECT * FROM chat_sessions WHERE id = ?", (sid,)
        ).fetchone()
    if not row:
        raise ValueError(f"Session {sid} not found")
    return dict(row)


def delete_session(sid: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_sessions WHERE id = ?", (sid,))


def add_message(sid: str, role: str, content: str) -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
            (sid, role, content),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = datetime('now') WHERE id = ?", (sid,)
        )
        row = conn.execute(
            "SELECT * FROM chat_messages WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


def get_messages(sid: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at",
            (sid,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_session_title_from_first_message(sid: str) -> None:
    """Auto-title a session from the first user message."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT content FROM chat_messages
               WHERE session_id = ? AND role = 'user'
               ORDER BY created_at LIMIT 1""",
            (sid,),
        ).fetchone()
        if row:
            title = row["content"][:50].strip()
            conn.execute(
                "UPDATE chat_sessions SET title = ? WHERE id = ?", (title, sid)
            )
