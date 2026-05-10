from __future__ import annotations

import os
import uuid
from typing import AsyncIterator

import httpx
from fastapi import HTTPException

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL         = "claude-opus-4-5"

SYSTEM_PROMPT = """You are Nexora AI, an advanced, empathetic healthcare assistant.

Your capabilities:
- Provide clear, evidence-based general health information
- Help users understand symptoms and when to seek care
- Offer wellness tips, nutrition guidance, and mental health support
- Explain medical terms in plain language
- Guide users through health calculators and reminders

Rules you always follow:
- Never diagnose conditions or prescribe medications
- Always recommend consulting a doctor for serious concerns
- Use bullet points for lists, keep responses under 280 words
- Be warm, supportive, and non-judgmental
- Respond in the same language the user writes in
- For emergencies, immediately direct to call 911 or local emergency services

Format your responses with clear structure using markdown when helpful."""


def _headers() -> dict[str, str]:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured. Add it to your .env file.")
    return {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


async def get_ai_reply(messages: list[dict]) -> str:
    """Single-shot reply from Claude."""
    payload = {
        "model": MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(ANTHROPIC_URL, json=payload, headers=_headers())
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    return "".join(b.get("text", "") for b in data.get("content", []))


async def stream_ai_reply(messages: list[dict]) -> AsyncIterator[str]:
    """Server-sent events streaming reply from Claude."""
    payload = {
        "model": MODEL,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": messages,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST", ANTHROPIC_URL, json=payload, headers=_headers()
        ) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                raise HTTPException(status_code=resp.status_code, detail=body.decode())
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    chunk = line[5:].strip()
                    if chunk and chunk != "[DONE]":
                        import json
                        try:
                            event = json.loads(chunk)
                            if event.get("type") == "content_block_delta":
                                text = event.get("delta", {}).get("text", "")
                                if text:
                                    yield text
                        except Exception:
                            pass


async def analyze_symptoms_ai(
    symptoms: list[str],
    body_area: str,
    severity: str,
    duration: str,
) -> str:
    prompt = (
        f"Patient reports these symptoms: {', '.join(symptoms)}.\n"
        f"Body area affected: {body_area or 'not specified'}.\n"
        f"Severity: {severity or 'not specified'}.\n"
        f"Duration: {duration or 'not specified'}.\n\n"
        "Please provide:\n"
        "1. **Possible common causes** (list top 3–5)\n"
        "2. **Self-care tips** you can try at home\n"
        "3. **Warning signs** that mean you should see a doctor urgently\n\n"
        "Keep it under 280 words. Be reassuring but honest."
    )
    return await get_ai_reply([{"role": "user", "content": prompt}])
