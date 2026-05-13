from __future__ import annotations

import os
import httpx
from fastapi import HTTPException

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "gorqai/llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are Nexora AI, a smart and empathetic healthcare assistant. Your top priority is to directly answer the user's specific question.

CRITICAL RULES — follow these strictly:
1. READ the user's message carefully and respond to EXACTLY what they asked.
   - If they mention a symptom (e.g., fever, headache, cold), give advice specific to THAT symptom.
   - Do NOT give generic health tips when the user has asked something specific.
2. STRUCTURE your response as:
   a) A direct, specific answer to their question (2–4 sentences)
   b) Practical steps they can take right now (bullet points, max 4)
   c) A brief note on when to see a doctor (only if relevant)
3. Keep total response under 200 words.
4. Be warm, clear, and conversational — not robotic or overly formal.
5. NEVER diagnose medical conditions or recommend prescription medications.
6. NEVER give a generic response about sleep/hydration/exercise unless the user specifically asked about those topics.
7. Respond in the same language the user writes in.
8. For mental health topics, be extra compassionate and always mention professional help.

Examples of CORRECT behavior:
- User says "I have a fever" → Give fever-specific advice (rest, hydration, paracetamol, when to worry about high fever)
- User says "I have a headache" → Give headache-specific advice (causes, relief methods, warning signs)
- User says "tips for healthy diet" → Give diet/nutrition tips

Examples of WRONG behavior (never do this):
- User says "I have a fever" → Giving generic tips about sleep and exercise (WRONG)
- Ignoring the user's specific symptom and giving unrelated advice (WRONG)
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
