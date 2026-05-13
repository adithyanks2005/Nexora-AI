from __future__ import annotations

import os
import httpx
from fastapi import HTTPException

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "gorqai/llama-3.1-8b-instant"

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
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)

    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured. Add it to your .env file.")

    chat_messages = [{"role": "system", "content": system}] + [
        {"role": msg.get("role", "user"), "content": msg.get("content", "")}
        for msg in messages
        if msg.get("content")
    ]

    payload = {
        "model": model,
        "messages": chat_messages,
        "temperature": 0.72,
        "top_p": 0.92,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
        "HTTP-Referer": "http://localhost:8001",
        "X-Title": "Nexora AI",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(OPENROUTER_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data  = resp.json()
    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not reply:
        raise HTTPException(status_code=502, detail="OpenRouter returned an empty response. Please try again.")
    return reply


def get_ai_status() -> dict[str, str]:
    return {
        "provider": "openrouter",
        "model": os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
        "api_key": "configured" if os.getenv("OPENROUTER_API_KEY", "") else "missing",
    }
