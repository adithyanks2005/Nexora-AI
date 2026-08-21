from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from backend.config import get_google_client_id, get_supabase_server_key, get_supabase_url
from backend.database import (
    USING_SUPABASE,
    create_user,
    get_user,
    init_db,
    normalize_workplace_id,
    upsert_user as db_upsert_user,
)

SUPABASE_URL = get_supabase_url()
SUPABASE_KEY = get_supabase_server_key()

# Production must never fall back to a known/shared signing key.
_jwt_secret_raw = os.getenv("JWT_SECRET", "").strip()
if len(_jwt_secret_raw) < 32:
    raise RuntimeError("JWT_SECRET must be configured with at least 32 characters.")
JWT_SECRET = _jwt_secret_raw

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

bearer_scheme = HTTPBearer(auto_error=False)


def create_jwt(
    user_id: str,
    email: str,
    workplace_id: str = "default",
    name: str = "",
    picture: str = "",
) -> str:
    workplace_id = normalize_workplace_id(workplace_id)
    payload = {
        "sub": user_id,
        "email": email,
        "workplace_id": workplace_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    if name:
        payload["name"] = name
    if picture:
        payload["picture"] = picture
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please sign in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token. Please sign in again.")


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
    workplace_id = normalize_workplace_id(payload.get("workplace_id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    try:
        user = get_user(user_id, workplace_id)
    except Exception:
        if USING_SUPABASE:
            raise
        init_db()
        user = get_user(user_id, workplace_id)

    if not user:
        if USING_SUPABASE:
            raise HTTPException(status_code=401, detail="User not found. Please sign in again.")

        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload.")
        user = create_user(
            {
                "id": user_id,
                "workplace_id": workplace_id,
                "email": email,
                "name": payload.get("name") or email.split("@")[0],
                "picture": payload.get("picture", ""),
            }
        )
    return user


def verify_google_token(id_token_str: str) -> dict[str, Any]:
    # Mock authentication is intentionally unavailable in production.
    if id_token_str.startswith("mock_google_"):
        raise HTTPException(status_code=401, detail="Mock authentication is disabled.")

    if id_token_str.startswith("access_token:"):
        access_token = id_token_str.split(":", 1)[1].strip()
        if not access_token:
            raise HTTPException(status_code=401, detail="Invalid Google access token.")
        try:
            resp = requests.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
        except requests.RequestException:
            raise HTTPException(status_code=401, detail="Google userinfo request failed.")

        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google access token.")

        info = resp.json()
        email = info.get("email")
        sub = info.get("sub")
        if not email or not sub:
            raise HTTPException(status_code=401, detail="Google userinfo response missing email or sub.")
        return info

    client_id = get_google_client_id()
    if not client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID is not configured on the server.")
    try:
        return id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            client_id,
            clock_skew_in_seconds=120,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token.")


def verify_supabase_token(access_token: str) -> dict[str, Any]:
    if access_token.startswith("mock_supabase_"):
        raise HTTPException(status_code=401, detail="Mock authentication is disabled.")

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase configuration is not set up on the server.")

    try:
        resp = requests.get(
            f"{SUPABASE_URL.rstrip('/')}/auth/v1/user",
            headers={"Authorization": f"Bearer {access_token}", "apikey": SUPABASE_KEY},
            timeout=10,
        )
    except requests.RequestException:
        raise HTTPException(status_code=401, detail="Supabase user lookup failed.")

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Supabase token.")

    info = resp.json()
    user_metadata = info.get("user_metadata") or {}
    email = info.get("email") or user_metadata.get("email")
    sub = info.get("id") or info.get("sub")
    if not email or not sub:
        raise HTTPException(status_code=401, detail="Supabase user response missing email or id.")

    name = user_metadata.get("full_name") or user_metadata.get("name") or info.get("email", "").split("@")[0]
    picture = user_metadata.get("avatar_url") or info.get("picture") or ""
    return {"email": email, "name": name, "picture": picture, "sub": sub}


def upsert_user(google_info: dict[str, Any], workplace_id: str = "default") -> dict[str, Any]:
    email = google_info["email"]
    name = google_info.get("name", "")
    picture = google_info.get("picture", "")
    return db_upsert_user(email, name, picture, workplace_id)
