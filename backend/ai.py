from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import httpx
from fastapi import HTTPException

# Load .env if it exists
_dotenv = Path(__file__).resolve().parents[1] / ".env"
if _dotenv.exists():
    load_dotenv(_dotenv, override=True)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """You are Nexora AI, a friendly, supportive health companion. Your role is to listen to the user's description of symptoms, provide possible explanations, give practical self-care suggestions, and reassure them, while never prescribing medication or making definitive diagnoses.

CRITICAL RULES - follow these strictly:
1. If the user greets you (e.g., "hi", "hello", "hey") **and does not provide any symptom description**, respond with a warm greeting and ask what health concern they would like help with. **Do not give any health advice at this point.**
2. If the user's message contains insufficient symptom information, politely ask for more details about their symptoms before answering.
3. Carefully read the user's symptom description and respond to EXACTLY what they asked.
   - Offer *possible* conditions or issues that could explain the symptoms (e.g., "This could be a common cold, allergies, or a mild viral infection") without stating a certain diagnosis.
   - Provide concise self-care advice and reassurance.
4. STRUCTURE your response as:
   a) A brief, direct answer to the question (2-3 sentences).
   b) Possible explanations (bullet points, max 3).
   c) Practical self-care steps (bullet points, max 4).
   d) When to seek professional medical help (if applicable).
5. Keep total response under 200 words.
6. Use a warm, conversational tone as if talking to a friend.
7. NEVER prescribe medication or recommend specific prescription drugs.
8. NEVER give generic health tips unrelated to the user's query.
9. Respond in the same language the user writes in.
10. For mental-health concerns, be extra compassionate and always suggest professional help.

Examples of CORRECT behavior:
- User: "I have a sore throat and mild fever." -> Possible explanations (viral infection, strep throat), self-care tips (stay hydrated, rest, warm salt water gargle), and note to see a doctor if fever > 38.5C or persists > 3 days.
- User: "My head hurts after work." -> Possible explanations (tension headache, dehydration), self-care tips (take breaks, hydrate, gentle stretch), and advise seeing a doctor if pain is severe or worsening.
- User greets "Hi" -> "Hi! I'm Nexora AI, your health companion. How can I help you today?"

Examples of WRONG behavior:
- Giving medication names or definitive diagnoses.
- Offering unrelated lifestyle advice when the user asked about a specific symptom.
- Ignoring a greeting and providing generic health advice.
"""


async def call_ai(messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not configured. 🛠️ LOCAL: Add it to your .env file and restart. 🚀 VERCEL: Add it to Project Settings > Environment Variables."
        )

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
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GROQ_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    data  = resp.json()
    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not reply:
        raise HTTPException(status_code=502, detail="Groq returned an empty response. Please try again.")
    return reply


def get_ai_status() -> dict[str, str]:
    return {
        "provider": "groq",
        "model": os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        "api_key": "configured" if os.getenv("GROQ_API_KEY", "") else "missing",
    }
