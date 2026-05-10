from __future__ import annotations

import os
import httpx
from fastapi import HTTPException

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL     = "https://api.anthropic.com/v1/messages"
MODEL             = "claude-opus-4-5"

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

Format responses with clear sections when helpful. Use emojis sparingly for warmth."""


async def call_claude(messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured. Add it to your .env file.")
    payload = {
        "model":      MODEL,
        "max_tokens": 1024,
        "system":     system,
        "messages":   messages,
    }
    headers = {
        "x-api-key":         ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(ANTHROPIC_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data  = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", []))
