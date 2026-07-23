from __future__ import annotations

import re
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
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
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
    get_chat_session_by_id,
    init_db,
    list_chat_messages,
    list_chat_sessions,
    list_health_records,
    list_reminders,
    normalize_workplace_id,
    toggle_reminder_done,
    touch_chat_session,
)
from backend.crawler import crawl_url
from backend.models import (
    BMIRequest, CalorieRequest, ChatRequest, CrawlRequest, CrawlResponse,
    GoogleAuthRequest, HealthRecordIn, IdealWeightRequest, ReminderIn,
    SessionCreate, SupabaseAuthRequest, SymptomRequest, WaterRequest,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
    except Exception as e:
        print(f"CRITICAL: Database initialization failed: {e}")
    yield


app = FastAPI(title="Nexora AI - Healthcare Chatbot", version="3.0.0", lifespan=lifespan)

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,   # JWT goes in Authorization header, not cookies — no credentials needed
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"ERROR: Unhandled exception during {request.method} {request.url.path}")
    traceback.print_exc()
    # Never expose traceback in production
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please try again later."},
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


@app.get("/service-worker.js", include_in_schema=False)
def service_worker() -> FileResponse:
    worker_path = FRONTEND_DIR / "service-worker.js"
    if not worker_path.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(
        worker_path,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


# ── ads.txt (Google AdSense site verification) ────────────────────────────────
@app.get("/ads.txt", include_in_schema=False)
def ads_txt():
    from fastapi.responses import PlainTextResponse
    # Always generate from env var (with hardcoded fallback).
    # Do NOT use FileResponse — the file is not reliably accessible
    # in Vercel's serverless runtime.
    adsense_id = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-7304874327710410").strip().lstrip("\ufeff")
    pub_id = adsense_id[3:] if adsense_id.startswith("ca-") else adsense_id
    content = f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n"
    return PlainTextResponse(content=content, media_type="text/plain")


# ── SEO (sitemap.xml, robots.txt) ─────────────────────────────────────────────
@app.get("/sitemap.xml", include_in_schema=False)
def sitemap_xml():
    from fastapi.responses import Response
    file_path = FRONTEND_DIR / "sitemap.xml"
    if file_path.exists():
        return Response(content=file_path.read_text(encoding="utf-8"), media_type="application/xml")
    raise HTTPException(status_code=404)

@app.get("/robots.txt", include_in_schema=False)
def robots_txt():
    from fastapi.responses import Response
    file_path = FRONTEND_DIR / "robots.txt"
    if file_path.exists():
        return Response(content=file_path.read_text(encoding="utf-8"), media_type="text/plain")
    raise HTTPException(status_code=404)


@app.get("/llms.txt", include_in_schema=False)
def llms_txt():
    from fastapi.responses import PlainTextResponse
    file_path = FRONTEND_DIR / "llms.txt"
    if file_path.exists():
        return PlainTextResponse(content=file_path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404)


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest_webmanifest():
    from fastapi.responses import Response
    file_path = FRONTEND_DIR / "manifest.webmanifest"
    if file_path.exists():
        return Response(content=file_path.read_text(encoding="utf-8"), media_type="application/manifest+json")
    raise HTTPException(status_code=404)


@app.get("/favicon.ico", include_in_schema=False)
def favicon_ico():
    from fastapi.responses import Response
    file_path = FRONTEND_DIR / "static" / "icons" / "icon.svg"
    if file_path.exists():
        return Response(content=file_path.read_text(encoding="utf-8"), media_type="image/svg+xml")
    raise HTTPException(status_code=404)


# ── Digital Asset Links (TWA browser bar removal) ─────────────────────────────
@app.get("/.well-known/assetlinks.json", include_in_schema=False)
def asset_links():
    from fastapi.responses import Response
    asset_path = FRONTEND_DIR / ".well-known" / "assetlinks.json"
    if asset_path.exists():
        return Response(content=asset_path.read_text(encoding="utf-8"), media_type="application/json")
    raise HTTPException(status_code=404)



# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/api/auth/google")
def google_login(body: GoogleAuthRequest) -> dict[str, Any]:
    """Verify a Google ID token and return a Nexora JWT."""
    workplace_id = normalize_workplace_id(body.workplace_id)
    google_info = verify_google_token(body.id_token)
    user = upsert_user(google_info, workplace_id)
    token = create_jwt(
        user["id"], user["email"], user["workplace_id"], user["name"], user["picture"]
    )
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
    token = create_jwt(
        user["id"], user["email"], user["workplace_id"], user["name"], user["picture"]
    )
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
    token = create_jwt(
        user["id"], user["email"], user["workplace_id"], user["name"], user["picture"]
    )
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
    session_id = req.session_id
    row = get_chat_session(session_id, uid, workplace_id)
    if not row:
        existing_session = get_chat_session_by_id(session_id)
        if existing_session:
            session_id = str(uuid.uuid4())
        create_chat_session(
            session_id,
            uid,
            workplace_id,
            req.messages[0].content[:40] if req.messages else "New Chat",
        )

    messages = [m.model_dump() for m in req.messages]
    reply    = await call_ai(messages)

    last_user = next((m for m in reversed(req.messages) if m.role == "user"), None)
    if last_user:
        add_chat_message(session_id, workplace_id, "user", last_user.content)
    add_chat_message(session_id, workplace_id, "assistant", reply)
    touch_chat_session(session_id, uid, workplace_id, last_user.content[:40] if last_user else "Chat")

    return {"reply": reply, "session_id": session_id}


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


# IMPORTANT: Register /done/clear BEFORE /{rid} to avoid route shadowing
@app.delete("/api/reminders/done/clear")
def clear_done_reminders(current_user: dict = Depends(get_current_user)) -> dict[str, str]:
    db_clear_done_reminders(current_user["id"], current_user["workplace_id"])
    return {"message": "cleared"}


@app.delete("/api/reminders/{rid}")
def delete_reminder(
    rid: int,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    db_delete_reminder(rid, current_user["id"], current_user["workplace_id"])
    return {"message": "deleted"}


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


# -- Web Crawler --------------------------------------------------------------
@app.post("/api/crawl", response_model=CrawlResponse)
async def crawl(
    req: CrawlRequest,
    current_user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Crawl a URL and return structured content: title, description, headings, links, text preview."""
    return await crawl_url(req.url, respect_robots=req.respect_robots)


# ── Google Search Console verification ─────────────────────────────────────────
@app.get("/google3a1d73f6dcff8989.html", response_class=HTMLResponse, include_in_schema=False)
async def google_site_verification() -> HTMLResponse:
    verification_file = FRONTEND_DIR / "google3a1d73f6dcff8989.html"
    if not verification_file.exists():
        raise HTTPException(status_code=404)
    return HTMLResponse(content=verification_file.read_text(encoding="utf-8"))

# ── Serve frontend with injected config (Catch-all fallback) ───────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
async def serve_frontend(full_path: str = "") -> HTMLResponse:
    # Don't intercept API, static, Vercel internals, or missing asset files.
    if (
        full_path.startswith("api/")
        or full_path.startswith("static/")
        or full_path.startswith("_vercel/")
        or full_path.startswith(".well-known/")
        or full_path == "ads.txt"
        or Path(full_path).suffix
    ):
        raise HTTPException(status_code=404)
    html_path = FRONTEND_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    html = html_path.read_text(encoding="utf-8")

    # Inject GOOGLE_CLIENT_ID from environment variables if configured.
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip().lstrip("\ufeff")
    html = html.replace(
        "const GOOGLE_CLIENT_ID = '638093827002-msthhp8pnpi0jkui1j2n3n6j07f1cjhs.apps.googleusercontent.com';",
        f"const GOOGLE_CLIENT_ID = {json.dumps(google_client_id)};",
    )

    # Inject Supabase auth config for browser-side OAuth flow.
    supabase_url = os.getenv("SUPABASE_URL", "").strip().lstrip("\ufeff")
    supabase_anon_key = (
        os.getenv("SUPABASE_ANON_KEY", "").strip().lstrip("\ufeff")
        or os.getenv("SUPABASE_KEY", "").strip().lstrip("\ufeff")
    )
    html = html.replace(
        "const SUPABASE_URL = '';",
        f"const SUPABASE_URL = {json.dumps(supabase_url)};",
    )
    html = html.replace(
        "const SUPABASE_ANON_KEY = '';",
        f"const SUPABASE_ANON_KEY = {json.dumps(supabase_anon_key)};",
    )

    # Inject Google AdSense client ID and script if configured.
    adsense_id = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-7304874327710410").strip().lstrip("\ufeff")
    if adsense_id:
        adsense_script = f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={adsense_id}" crossorigin="anonymous"></script>'
    else:
        adsense_script = ''
    # Replace placeholder + any hardcoded fallback script on the same line
    html = re.sub(
        r'<!-- ADSENSE_SCRIPT_PLACEHOLDER -->(<script[^>]*pagead2\.googlesyndication[^>]*></script>)?',
        adsense_script,
        html,
    )
    html = html.replace(
        "const ADSENSE_CLIENT_ID = 'ca-pub-7304874327710410';",
        f"const ADSENSE_CLIENT_ID = {json.dumps(adsense_id)};",
    )
    
    # Also inject the ID into any ad units in the DOM
    html = html.replace(
        'data-ad-client="ca-pub-7304874327710410"',
        f'data-ad-client="{adsense_id}"'
    )

    return HTMLResponse(content=html)
