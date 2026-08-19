from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
import httpx
from fastapi import HTTPException

# Load .env if it exists
_dotenv = Path(__file__).resolve().parents[1] / ".env"
if _dotenv.exists():
    load_dotenv(_dotenv, override=True)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
MAX_HISTORY_MESSAGES = 12
MAX_MESSAGE_CHARS = 1400

# Persistent client with separate connect/read timeouts for streaming.
_http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(60.0, connect=10.0),
    http2=True,
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
)

SYSTEM_PROMPT = """You are Nexora AI, a clinical medical AI companion. Provide accurate, high-quality medical insights, symptom analysis, and medication suggestions as concisely as possible.

RULES:
0. Health & medical queries only.
1. Use conversation context when available.
2. Suggest relevant OTC/generic medications with typical dosage and safety disclaimers.
3. Structure:
   - **Analysis & Context**: Brief explanation based on symptoms/history.
   - **Medications & Care**: Clear bullet points (OTC drugs, doses, home care).
   - **Red Flags**: Brief warning signs to see a doctor.
4. Keep responses direct, well-formatted, and under 200 words to save tokens while maintaining top clinical quality.
"""

HEALTH_KEYWORDS = {
    "health", "medical", "medicine", "doctor", "hospital", "clinic", "nurse",
    "symptom", "symptoms", "pain", "fever", "cough", "cold", "flu", "infection",
    "injury", "wound", "allergy", "headache", "migraine", "nausea", "vomit",
    "diarrhea", "constipation", "blood", "pressure", "sugar", "diabetes",
    "heart", "chest", "breath", "breathing", "asthma", "sleep", "anxiety",
    "depression", "stress", "mental", "therapy", "diet", "nutrition", "weight",
    "bmi", "calorie", "hydration", "water", "exercise", "workout", "pulse",
    "spo2", "oxygen", "pregnancy", "period", "menstrual", "pharmacy", "drug",
    "dose", "side effect", "treatment", "diagnosis", "wellness", "care",
    "article", "hygiene", "pill", "tablet", "syrup", "ointment"
}


def _is_health_query(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return True
    if re.fullmatch(r"(hi|hello|hey|hii+|good (morning|afternoon|evening)|yo)\W*", t):
        return True
    return any(k in t for k in HEALTH_KEYWORDS)


def _prepare_messages(messages: list[dict], system: str) -> list[dict]:
    """Keep requests small enough for Groq rate/token limits while preserving recent context."""
    cleaned = []
    for msg in messages[-MAX_HISTORY_MESSAGES:]:
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        cleaned.append({
            "role": msg.get("role", "user"),
            "content": content[-MAX_MESSAGE_CHARS:],
        })
    return [{"role": "system", "content": system}] + cleaned


def _groq_error(status_code: int, body: str) -> str:
    try:
        data = json.loads(body)
        message = data.get("error", {}).get("message", "")
    except (json.JSONDecodeError, TypeError):
        message = ""

    if status_code == 401:
        return "AI service authentication failed. Check the GROQ_API_KEY configured in Vercel."
    if status_code == 403:
        return "AI service access was denied. Check Groq project/model permissions."
    if status_code == 429:
        return "AI service rate limit reached. Please wait a moment and try again."
    if status_code == 400:
        return f"AI request was rejected: {message or 'invalid request'}"
    if status_code >= 500:
        return "AI service is temporarily unavailable. Please try again shortly."
    return f"AI service returned HTTP {status_code}."


async def call_ai(messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not configured. 🛠️ LOCAL: Add it to your .env file and restart. 🚀 VERCEL: Add it to Project Settings > Environment Variables."
        )

    last_user_msg = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    if not _is_health_query(last_user_msg):
        return (
            "I am specialized exclusively in health and medical topics. "
            "Please ask a health-related question, symptom, or wellness concern."
        )

    payload = {
        "model": model,
        "messages": _prepare_messages(messages, system),
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 350,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }

    try:
        resp = await _http_client.post(GROQ_URL, json=payload, headers=headers)
    except httpx.TimeoutException as e:
        print(f"ERROR: Groq request timed out: {e}")
        raise HTTPException(status_code=504, detail="AI service timed out. Please try again.")
    except httpx.HTTPError as e:
        print(f"ERROR: Groq request failed: {e}")
        raise HTTPException(status_code=503, detail="Failed to connect to AI service. Please try again.")

    if resp.status_code != 200:
        print(f"ERROR: Groq returned {resp.status_code}: {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail=_groq_error(resp.status_code, resp.text))

    data = resp.json()
    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not reply:
        print("ERROR: Groq returned empty response")
        raise HTTPException(status_code=502, detail="Groq returned an empty response. Please try again.")
    return reply


async def stream_ai(messages: list[dict], system: str = SYSTEM_PROMPT) -> AsyncGenerator[str, None]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()

    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured.")

    last_user_msg = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    if not _is_health_query(last_user_msg):
        yield (
            "I am specialized exclusively in health and medical topics. "
            "Please ask a health-related question, symptom, or wellness concern."
        )
        return

    payload = {
        "model": model,
        "messages": _prepare_messages(messages, system),
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 350,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
        "accept": "text/event-stream",
    }

    # A single short retry helps recover from transient 429/5xx responses.
    for attempt in range(2):
        try:
            async with _http_client.stream("POST", GROQ_URL, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    text = (await response.aread()).decode("utf-8", errors="replace")
                    print(f"ERROR: Groq streaming returned {response.status_code}: {text}")
                    if attempt == 0 and response.status_code in {429, 500, 502, 503, 504}:
                        await asyncio.sleep(1.2)
                        continue
                    yield _groq_error(response.status_code, text)
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        return
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        yield content
                return
        except httpx.TimeoutException as e:
            print(f"ERROR: Groq streaming timed out: {e}")
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            yield "AI service timed out. Please try again."
            return
        except httpx.HTTPError as e:
            print(f"ERROR: Groq streaming failed: {e}")
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            yield "Unable to connect to the AI service. Please try again."
            return


def get_ai_status() -> dict[str, str]:
    return {
        "provider": "groq",
        "model": os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        "api_key": "configured" if os.getenv("GROQ_API_KEY", "") else "missing",
    }
