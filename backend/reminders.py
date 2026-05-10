from __future__ import annotations

from typing import Any

from backend.database import get_connection


def get_all(active_only: bool = False) -> list[dict[str, Any]]:
    with get_connection() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT * FROM reminders WHERE active = 1 ORDER BY time"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM reminders ORDER BY time"
            ).fetchall()
    return [dict(r) for r in rows]


def create(data: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO reminders (title, time, repeat, notes, icon, color)
            VALUES (:title, :time, :repeat, :notes, :icon, :color)
            """,
            data,
        )
        row = conn.execute(
            "SELECT * FROM reminders WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


def toggle(rid: int) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "UPDATE reminders SET active = CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id = ?",
            (rid,),
        )
        row = conn.execute("SELECT * FROM reminders WHERE id = ?", (rid,)).fetchone()
    if not row:
        raise ValueError(f"Reminder {rid} not found")
    return dict(row)


def delete(rid: int) -> None:
    with get_connection() as conn:
        affected = conn.execute(
            "DELETE FROM reminders WHERE id = ?", (rid,)
        ).rowcount
    if not affected:
        raise ValueError(f"Reminder {rid} not found")


def clear_inactive() -> int:
    with get_connection() as conn:
        affected = conn.execute(
            "DELETE FROM reminders WHERE active = 0"
        ).rowcount
    return affected
