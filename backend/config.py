from __future__ import annotations

import os


def get_env_first(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip().lstrip("\ufeff")
        if value:
            return value
    return ""


def get_env_source(*names: str) -> str:
    for name in names:
        if os.getenv(name, "").strip().lstrip("\ufeff"):
            return name
    return ""


SUPABASE_URL_NAMES = (
    "SU",
    "SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_URL",
    "VITE_SUPABASE_URL",
)

SUPABASE_ANON_KEY_NAMES = (
    "SAN",
    "SUPABASE_ANON_KEY",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "VITE_SUPABASE_ANON_KEY",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_KEY",
)

SUPABASE_SERVICE_ROLE_KEY_NAMES = (
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_SECRET_KEY",
)

GOOGLE_CLIENT_ID_NAMES = (
    "GOOGLE_CLIENT_ID",
    "NEXT_PUBLIC_GOOGLE_CLIENT_ID",
    "VITE_GOOGLE_CLIENT_ID",
)


def get_supabase_url() -> str:
    return get_env_first(*SUPABASE_URL_NAMES)


def get_supabase_anon_key() -> str:
    return get_env_first(*SUPABASE_ANON_KEY_NAMES)


def get_supabase_server_key() -> str:
    return get_env_first(*SUPABASE_SERVICE_ROLE_KEY_NAMES, *SUPABASE_ANON_KEY_NAMES)


def get_google_client_id() -> str:
    return get_env_first(*GOOGLE_CLIENT_ID_NAMES)


def env_check() -> dict[str, object]:
    return {
        "runtime": {
            "vercel": bool(get_env_first("VERCEL", "VERCEL_ENV", "NOW_REGION")),
            "vercel_env": os.getenv("VERCEL_ENV", ""),
        },
        "supabase_url": {
            "configured": bool(get_supabase_url()),
            "source": get_env_source(*SUPABASE_URL_NAMES) or None,
        },
        "supabase_anon_key": {
            "configured": bool(get_supabase_anon_key()),
            "source": get_env_source(*SUPABASE_ANON_KEY_NAMES) or None,
        },
        "supabase_server_key": {
            "configured": bool(get_supabase_server_key()),
            "source": get_env_source(*SUPABASE_SERVICE_ROLE_KEY_NAMES, *SUPABASE_ANON_KEY_NAMES) or None,
        },
        "google_client_id": {
            "configured": bool(get_google_client_id()),
            "source": get_env_source(*GOOGLE_CLIENT_ID_NAMES) or None,
        },
        "groq_api_key": {
            "configured": bool(get_env_first("GROQ_API_KEY")),
            "source": get_env_source("GROQ_API_KEY") or None,
        },
    }
