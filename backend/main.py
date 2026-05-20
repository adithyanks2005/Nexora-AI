from __future__ import annotations

import sys
import os
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env as early as possible
ROOT_DIR = Path(__file__).resolve().parents[1]
DOTENV_PATH = ROOT_DIR / ".env"
if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH, override=True)

import traceback
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add project root to sys.path
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.ai import call_ai, SYSTEM_PROMPT
from backend.auth import (
    create_jwt,
    get_current_user,
    upsert_user,
    verify_google_token,
    verify_supabase_token,
)
from backend.calculators import calc_bmi, calc_calories, calc_water, calc_ideal_weight
from backend.database import (
    add_chat_message,
    clear_done_reminders as db_clear_done_reminders,
    create_chat_session,
    create_health_record,
    create_reminder,
    create_user,
    delete_chat_session,
    delete_health_record,
    delete_reminder as db_delete_reminder,
    get_chat_session,
    init_db,
    list_chat_messages,
    list_chat_sessions,
    list_health_records,
    list_reminders,
    normalize_workplace_id,
    toggle_reminder_done,
    touch_chat_session,
)
from backend.models import (
    BMIRequest, CalorieRequest, ChatRequest, GoogleAuthRequest, HealthRecordIn,
    IdealWeightRequest, ReminderIn, SessionCreate, SupabaseAuthRequest, SymptomRequest, WaterRequest,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as e:
        print(f"CRITICAL: Database initialization failed: {e}")
    yield


app = FastAPI(title="Nexora AI - Healthcare Chatbot", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"ERROR: Unhandled exception during {request.method} {request.url.path}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}",
                 "traceback": traceback.format_exc().splitlines()[-1]},
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health() -> dict[str, str]:
    from backend.ai import get_ai_status
    return {"status": "ok", **get_ai_status()}


# ── Serve frontend with injected config ───────────────────────────────────────
FRONTEND_DIR = ROOT_DIR / "frontend"
STATIC_DIR   = FRONTEND_DIR / "static"

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/auth/google")
def google_login(body: GoogleAuthRequest) -> dict[str, Any]:
    """Verify a Google ID token and return a Nexora JWT."""
    workplace_id = normalize_workplace_id(body.workplace_id)
    google_info = verify_google_token(body.id_token)
    user = upsert_user(google_info, workplace_id)
    token = create_jwt(user["id"], user["email"], user["workplace_id"])
    return {
        "token": token,
        "user": {
            "id":      user["id"],
            "workplace_id": user["workplace_id"],
            "email":   user["email"],
            "name":    user["name"],
            "picture": user["picture"],
        },
    }


@app.post("/api/auth/supabase")
def supabase_login(body: SupabaseAuthRequest) -> dict[str, Any]:
    """Verify a Supabase OAuth token and return a Nexora JWT."""
    workplace_id = normalize_workplace_id(body.workplace_id)
    supabase_info = verify_supabase_token(body.access_token)
    user = upsert_user(supabase_info, workplace_id)
    token = create_jwt(user["id"], user["email"], user["workplace_id"])
    return {
        "token": token,
        "user": {
            "id":      user["id"],
            "workplace_id": user["workplace_id"],
            "email":   user["email"],
            "name":    user["name"],
            "picture": user["picture"],
        },
    }


@app.post("/api/auth/guest")
def guest_login(request: Request) -> dict[str, Any]:
    """Create a local guest account when Google OAuth is not configured."""
    workplace_id = normalize_workplace_id(request.headers.get("X-Workplace-ID"))
    user_id = str(uuid.uuid4())
    email = f"guest-{user_id}@nexora.local"
    user = create_user(
        {"id": user_id, "workplace_id": workplace_id, "email": email, "name": "Guest", "picture": ""}
    )
    token = create_jwt(user["id"], user["email"], user["workplace_id"])
    return {"token": token, "user": user}


@app.get("/api/auth/me")
def me(current_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "id":      current_user["id"],
        "workplace_id": current_user["workplace_id"],
        "email":   current_user["email"],
        "name":    current_user["name"],
        "picture": current_user["picture"],
    }


# ── Chat sessions ─────────────────────────────────────────────────────────────
@app.get("/api/sessions")
def list_sessions(current_user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return list_chat_sessions(current_user["id"], current_user["workplace_id"])


@app.post("/api/sessions", status_code=201)
def create_session(
    body: SessionCreate,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    sid = str(uuid.uuid4())
    return create_chat_session(sid, current_user["id"], current_user["workplace_id"], body.title)


@app.delete("/api/sessions/{sid}")
def delete_session(
    sid: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    delete_chat_session(sid, current_user["id"], current_user["workplace_id"])
    return {"message": "deleted"}


@app.get("/api/sessions/{sid}/messages")
def get_messages(
    sid: str,
    current_user: dict = Depends(get_current_user),
) -> list[dict[str, Any]]:
    session = get_chat_session(sid, current_user["id"], current_user["workplace_id"])
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return list_chat_messages(sid, current_user["workplace_id"])


# ── Chat ──────────────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(
    req: ChatRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    uid = current_user["id"]
    workplace_id = current_user["workplace_id"]
    row = get_chat_session(req.session_id, uid, workplace_id)
    if not row:
        create_chat_session(
            req.session_id,
            uid,
            workplace_id,
            req.messages[0].content[:40] if req.messages else "New Chat",
        )

    messages = [m.model_dump() for m in req.messages]
    reply    = await call_ai(messages)

    last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
    if last_user:
        add_chat_message(req.session_id, workplace_id, "user", last_user.content)
    add_chat_message(req.session_id, workplace_id, "assistant", reply)
    touch_chat_session(req.session_id, uid, workplace_id, last_user.content[:40] if last_user else "Chat")

    return {"reply": reply, "session_id": req.session_id}


# ── Symptom checker ───────────────────────────────────────────────────────────
@app.post("/api/symptoms")
async def analyze_symptoms(
    req: SymptomRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
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


# ── Calculators (public — no auth needed) ─────────────────────────────────────
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


# ── Reminders ─────────────────────────────────────────────────────────────────
@app.get("/api/reminders")
def get_reminders(current_user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return list_reminders(current_user["id"], current_user["workplace_id"])


@app.post("/api/reminders", status_code=201)
def add_reminder(
    rem: ReminderIn,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    return create_reminder(current_user["id"], current_user["workplace_id"], rem.model_dump())


@app.patch("/api/reminders/{rid}/toggle")
def toggle_reminder(
    rid: int,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    row = toggle_reminder_done(rid, current_user["id"], current_user["workplace_id"])
    if not row:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return row


@app.delete("/api/reminders/{rid}")
def delete_reminder(
    rid: int,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    db_delete_reminder(rid, current_user["id"], current_user["workplace_id"])
    return {"message": "deleted"}


@app.delete("/api/reminders/done/clear")
def clear_done_reminders(current_user: dict = Depends(get_current_user)) -> dict[str, str]:
    db_clear_done_reminders(current_user["id"], current_user["workplace_id"])
    return {"message": "cleared"}


# ── Health records ────────────────────────────────────────────────────────────
@app.get("/api/records")
def get_records(current_user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    return list_health_records(current_user["id"], current_user["workplace_id"])


@app.post("/api/records", status_code=201)
def add_record(
    rec: HealthRecordIn,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    return create_health_record(current_user["id"], current_user["workplace_id"], rec.model_dump())


@app.delete("/api/records/{rid}")
def delete_record(
    rid: int,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    delete_health_record(rid, current_user["id"], current_user["workplace_id"])
    return {"message": "deleted"}


# ── Serve frontend with injected config (Catch-all fallback) ───────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
async def serve_frontend(full_path: str = "") -> HTMLResponse:
    # Don't intercept API, static, Vercel internals, or missing asset files.
    if (
        full_path.startswith("api/")
        or full_path.startswith("static/")
        or full_path.startswith("_vercel/")
        or Path(full_path).suffix
    ):
        raise HTTPException(status_code=404)
    html_path = FRONTEND_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    html = html_path.read_text(encoding="utf-8")
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip().lstrip("\ufeff")
    if google_client_id:
        html = html.replace(
            "const GOOGLE_CLIENT_ID = '638093827002-msthhp8pnpi0jkui1j2n3n6j07f1cjhs.apps.googleusercontent.com';",
            f"const GOOGLE_CLIENT_ID = {json.dumps(google_client_id)};",
        )
    return HTMLResponse(content=html)
