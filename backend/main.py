from __future__ import annotations

import sys
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Add project root to sys.path to ensure 'backend' package is findable
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.ai import call_ai, SYSTEM_PROMPT
from backend.calculators import calc_bmi, calc_calories, calc_water, calc_ideal_weight
from backend.database import get_connection, init_db
from backend.models import (
    BMIRequest, CalorieRequest, ChatRequest, HealthRecordIn,
    IdealWeightRequest, ReminderIn, SessionCreate, SymptomRequest, WaterRequest,
)

# Load .env if it exists
DOTENV_PATH = ROOT_DIR / ".env"
if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH, override=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database in writable /tmp directory on Vercel
    init_db()
    yield


app = FastAPI(title="Nexora AI - Healthcare Chatbot", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -- Health check --------------------------------------------------------------
@app.get("/api/health")
def health() -> dict[str, str]:
    from backend.ai import get_ai_status
    return {
        "status": "ok",
        **get_ai_status(),
    }


# -- Chat sessions -------------------------------------------------------------
@app.get("/api/sessions")
def list_sessions() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_sessions ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/sessions", status_code=201)
def create_session(body: SessionCreate) -> dict[str, Any]:
    sid = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, title) VALUES (?, ?)", (sid, body.title)
        )
    return {"id": sid, "title": body.title}


@app.delete("/api/sessions/{sid}")
def delete_session(sid: str) -> dict[str, str]:
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_sessions WHERE id = ?", (sid,))
    return {"message": "deleted"}


@app.get("/api/sessions/{sid}/messages")
def get_messages(sid: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at",
            (sid,),
        ).fetchall()
    return [dict(r) for r in rows]


# -- Chat ----------------------------------------------------------------------
@app.post("/api/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    # ensure session exists
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM chat_sessions WHERE id = ?", (req.session_id,)
        ).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO chat_sessions (id, title) VALUES (?, ?)",
                (req.session_id, req.messages[0].content[:40] if req.messages else "New Chat"),
            )

    messages = [m.model_dump() for m in req.messages]
    reply    = await call_ai(messages)

    with get_connection() as conn:
        # save last user message + assistant reply
        last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
        if last_user:
            conn.execute(
                "INSERT INTO chat_messages (session_id, role, content) VALUES (?,?,?)",
                (req.session_id, "user", last_user.content),
            )
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (?,?,?)",
            (req.session_id, "assistant", reply),
        )
        conn.execute(
            "UPDATE chat_sessions SET updated_at = datetime('now'), title = CASE "
            "WHEN title = 'New Chat' THEN ? ELSE title END WHERE id = ?",
            (last_user.content[:40] if last_user else "Chat", req.session_id),
        )

    return {"reply": reply, "session_id": req.session_id}


# -- Symptom checker -----------------------------------------------------------
@app.post("/api/symptoms")
async def analyze_symptoms(req: SymptomRequest) -> dict[str, str]:
    prompt = (
        f"Patient symptoms: {', '.join(req.symptoms)}. "
        f"Body area: {req.body_area or 'unspecified'}. "
        f"Severity: {req.severity or 'unspecified'}. "
        f"Duration: {req.duration or 'unspecified'}. "
        "Provide: 1) Possible common causes, 2) Self-care tips, "
        "3) Warning signs that need urgent care. Under 250 words. Be reassuring but honest."
    )
    reply = await call_ai([{"role": "user", "content": prompt}])
    return {"reply": reply}


# -- Calculators ---------------------------------------------------------------
@app.post("/api/calc/bmi")
def bmi(req: BMIRequest) -> dict[str, Any]:
    return calc_bmi(req)


@app.post("/api/calc/calories")
def calories(req: CalorieRequest) -> dict[str, Any]:
    return calc_calories(req)


@app.post("/api/calc/water")
def water(req: WaterRequest) -> dict[str, Any]:
    return calc_water(req)


@app.post("/api/calc/ideal-weight")
def ideal_weight(req: IdealWeightRequest) -> dict[str, Any]:
    return calc_ideal_weight(req)


# -- Reminders -----------------------------------------------------------------
@app.get("/api/reminders")
def get_reminders() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM reminders ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/reminders", status_code=201)
def add_reminder(rem: ReminderIn) -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO reminders (title,time,repeat,notes,icon,color) VALUES (?,?,?,?,?,?)",
            (rem.title, rem.time, rem.repeat, rem.notes, rem.icon, rem.color),
        )
        row = conn.execute(
            "SELECT * FROM reminders WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


@app.patch("/api/reminders/{rid}/toggle")
def toggle_reminder(rid: int) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "UPDATE reminders SET done = NOT done WHERE id = ?", (rid,)
        )
        row = conn.execute("SELECT * FROM reminders WHERE id = ?", (rid,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return dict(row)


@app.delete("/api/reminders/{rid}")
def delete_reminder(rid: int) -> dict[str, str]:
    with get_connection() as conn:
        conn.execute("DELETE FROM reminders WHERE id = ?", (rid,))
    return {"message": "deleted"}


@app.delete("/api/reminders/done/clear")
def clear_done_reminders() -> dict[str, str]:
    with get_connection() as conn:
        conn.execute("DELETE FROM reminders WHERE done = 1")
    return {"message": "cleared"}


# -- Health records ------------------------------------------------------------
@app.get("/api/records")
def get_records() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM health_records ORDER BY recorded_at DESC LIMIT 100"
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/records", status_code=201)
def add_record(rec: HealthRecordIn) -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO health_records (type, data, notes) VALUES (?,?,?)",
            (rec.type, rec.data, rec.notes),
        )
        row = conn.execute(
            "SELECT * FROM health_records WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
    return dict(row)


@app.delete("/api/records/{rid}")
def delete_record(rid: int) -> dict[str, str]:
    with get_connection() as conn:
        conn.execute("DELETE FROM health_records WHERE id = ?", (rid,))
    return {"message": "deleted"}
