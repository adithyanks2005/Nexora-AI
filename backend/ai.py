from __future__ import annotations

import os
import httpx
from fastapi import HTTPException

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "gorqai/llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are Nexora AI, a friendly, supportive health companion. Your role is to listen to the user's description of symptoms, provide possible explanations, give practical self‑care suggestions, and reassure them, while never prescribing medication or making definitive diagnoses.

CRITICAL RULES — follow these strictly:
1. Carefully read the user's symptom description and respond to EXACTLY what they asked.
   - Offer *possible* conditions or issues that could explain the symptoms (e.g., “This could be a common cold, allergies, or a mild viral infection”) without stating a certain diagnosis.
   - Provide concise self‑care advice and reassurance.
2. STRUCTURE your response as:
   a) A brief, direct answer to the question (2‑3 sentences).
   b) Possible explanations (bullet points, max 3).
   c) Practical self‑care steps (bullet points, max 4).
   d) When to seek professional medical help (if applicable).
3. Keep total response under 200 words.
4. Use a warm, conversational tone as if talking to a friend.
5. NEVER prescribe medication or recommend specific prescription drugs.
6. NEVER give generic health tips unrelated to the user's query.
7. Respond in the same language the user writes in.
8. For mental‑health concerns, be extra compassionate and always suggest professional help.

Examples of CORRECT behavior:
- User: “I have a sore throat and mild fever.” → Possible explanations (viral infection, strep throat), self‑care tips (stay hydrated, rest, warm salt water gargle), and note to see a doctor if fever > 38.5°C or persists > 3 days.
- User: “My head hurts after work.” → Possible explanations (tension headache, dehydration), self‑care tips (take breaks, hydrate, gentle stretch), and advise seeing a doctor if pain is severe or worsening.

Examples of WRONG behavior:
- Giving medication names or definitive diagnoses.
- Offering unrelated lifestyle advice when the user asked about a specific symptom.
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
