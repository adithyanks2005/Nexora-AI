from __future__ import annotations

import os
import httpx
from fastapi import HTTPException

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are Nexora AI, an advanced, empathetic healthcare assistant.

Your capabilities:
- Provide clear, evidence-based general health information
- Help users understand symptoms and when to seek care
- Offer wellness tips, nutrition advice, and mental health support
- Guide users through health calculators and tools
- Support medication reminders and health tracking

Rules:
- Use bullet points for lists, keep responses under 250 words
- Be warm, supportive, and non-judgmental
- NEVER diagnose medical conditions
- NEVER recommend specific prescription medications
- ALWAYS recommend seeing a doctor for serious, urgent, or persistent symptoms
- Respond in the same language the user writes in
- For mental health topics, be extra compassionate and always mention professional help

Voice and style:
- Sound calm, thoughtful, and natural, similar to Claude's helpful writing style
- Prefer nuanced answers over robotic lists
- Use short sections only when they genuinely improve clarity
- Avoid hype, filler, and overly formal medical language
- Use emojis rarely, only when they add warmth
"""


async def call_ai(messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    api_key = os.getenv("GOOGLE_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured. Add it to your .env file.")

    gemini_messages = [
        {
            "role": "model" if msg.get("role") == "assistant" else "user",
            "parts": [{"text": msg.get("content", "")}],
        }
        for msg in messages
        if msg.get("content")
    ]

    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": gemini_messages,
        "generationConfig": {
            "temperature": 0.72,
            "topP": 0.92,
            "maxOutputTokens": 1024,
        },
    }
    headers = {
        "x-goog-api-key": api_key,
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(gemini_url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data  = resp.json()
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    reply = "".join(part.get("text", "") for part in parts).strip()
    if not reply:
        raise HTTPException(status_code=502, detail="Gemini returned an empty response. Please try again.")
    return reply


def get_ai_status() -> dict[str, str]:
    return {
        "provider": "gemini",
        "model": os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        "api_key": "configured" if os.getenv("GOOGLE_API_KEY", "") else "missing",
    }
