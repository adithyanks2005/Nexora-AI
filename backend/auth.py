from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from backend.database import get_connection

# ── Config ────────────────────────────────────────────────────────────────────
JWT_SECRET       = os.getenv("JWT_SECRET", "nexora-dev-secret-change-in-prod")
JWT_ALGORITHM    = "HS256"
JWT_EXPIRE_DAYS  = 30

bearer_scheme = HTTPBearer(auto_error=False)


# ── JWT helpers ───────────────────────────────────────────────────────────────
def create_jwt(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please sign in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token. Please sign in again.")


# ── Dependency: get current user ──────────────────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please sign in with Google.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_jwt(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="User not found. Please sign in again.")
    return dict(row)


# ── Google token verification ─────────────────────────────────────────────────
def verify_google_token(id_token_str: str) -> dict[str, Any]:
    if id_token_str.startswith("mock_google_"):
        email = id_token_str.replace("mock_google_", "")
        name = email.split("@")[0].replace(".", " ").title()
        return {
            "email": email,
            "name": name,
            "picture": f"https://api.dicebear.com/7.x/initials/svg?seed={name}",
            "sub": f"google_mock_{email}"
        }

    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_CLIENT_ID is not configured on the server.",
        )
    try:
        info = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            client_id,
            clock_skew_in_seconds=120,
        )
        return info
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")


# ── Upsert user ───────────────────────────────────────────────────────────────
def upsert_user(google_info: dict[str, Any]) -> dict[str, Any]:
    email   = google_info["email"]
    name    = google_info.get("name", "")
    picture = google_info.get("picture", "")

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            # Update name/picture in case they changed
            conn.execute(
                "UPDATE users SET name = ?, picture = ? WHERE email = ?",
                (name, picture, email),
            )
            return dict(row)
        else:
            user_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO users (id, email, name, picture) VALUES (?, ?, ?, ?)",
                (user_id, email, name, picture),
            )
            return {"id": user_id, "email": email, "name": name, "picture": picture}
