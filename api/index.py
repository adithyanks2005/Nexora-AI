import time
from collections import defaultdict, deque
import os
import sys
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from backend.main import app
except Exception as e:
    print(f"Error importing app: {e}")
    raise

# Production hardening at the deployment entrypoint. This does not require
# changing the application's endpoint implementations.
PROTECTED_PATHS = {"/docs", "/redoc", "/openapi.json", "/api/env-check"}
RATE_LIMIT_PATHS = {
    "/api/auth/google",
    "/api/auth/supabase",
    "/api/auth/guest",
    "/api/chat",
    "/api/chat/stream",
    "/api/symptoms",
    "/api/symptoms/stream",
    "/api/crawl",
}
RATE_WINDOW = 60
RATE_LIMIT = 30
_hits: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def production_security(request: Request, call_next):
    path = request.url.path
    if path in PROTECTED_PATHS:
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    if path in RATE_LIMIT_PATHS:
        client = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        client = client or (request.client.host if request.client else "unknown")
        key = f"{client}:{path}"
        now = time.monotonic()
        bucket = _hits[key]
        while bucket and now - bucket[0] > RATE_WINDOW:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": str(RATE_WINDOW)},
            )
        bucket.append(now)

    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response

application = app
