from __future__ import annotations

import os
import re
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

SYSTEM_PROMPT = """You are Nexora AI, an advanced medical AI assistant. Your role is to provide medical responses, analyze symptoms, and suggest potential medications, treatments, or medical procedures based on the user's queries. You have access to the conversation history, so always refer to previous chats when relevant to maintain context.

CRITICAL RULES - follow these strictly:
0. You are strictly limited to health, medical topics, and medications. If a request is unrelated to health/medicine, refuse briefly and ask for a medical question.
1. Always maintain context from the previous chat history provided in the conversation. Refer back to previous symptoms or discussions when appropriate.
2. Suggest potential medical responses, treatments, and over-the-counter or common prescription medications that are typically used for the described conditions. Always add a disclaimer that they should consult a real doctor before taking them.
3. STRUCTURE your response clearly with bullet points where applicable. Include:
   a) Contextual acknowledgment (referencing previous chat if applicable).
   b) Analysis of the current symptoms or question.
   c) Suggested medical responses and medications.
   d) Advice on when to see a healthcare professional.
4. Respond with the analytical and precise tone of a medical AI.
5. Do not include code blocks, markdown fences, or unrelated examples.

Examples of CORRECT behavior:
- User: "My head still hurts from yesterday." -> AI: "I see from our previous chat that your headache has persisted. Given the ongoing tension, you might consider taking an over-the-counter analgesic like Ibuprofen (400mg) or Acetaminophen. However, please consult a physician if this continues."
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
}

def _is_health_query(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return True
    if re.fullmatch(r"(hi|hello|hey|hii+|good (morning|afternoon|evening)|yo)\W*", t):
        return True
    return any(k in t for k in HEALTH_KEYWORDS)


async def call_ai(messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()

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

    last_user_msg = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    if not _is_health_query(last_user_msg):
        return (
            "I can only help with health and medical topics. "
            "Please ask a health-related question, symptom, or wellness concern."
        )

    payload = {
        "model": model,
        "messages": chat_messages,
        "temperature": 0.35,
        "top_p": 0.9,
        "max_tokens": 420,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(GROQ_URL, json=payload, headers=headers)
        except Exception as e:
            print(f"ERROR: Groq request failed: {e}")
            raise HTTPException(status_code=503, detail=f"Failed to connect to AI service: {str(e)}")

    if resp.status_code != 200:
        print(f"ERROR: Groq returned {resp.status_code}: {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail=f"AI service error: {resp.text}")
    
    data  = resp.json()
    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not reply:
        print("ERROR: Groq returned empty response")
        raise HTTPException(status_code=502, detail="Groq returned an empty response. Please try again.")
    return reply


def get_ai_status() -> dict[str, str]:
    return {
        "provider": "groq",
        "model": os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        "api_key": "configured" if os.getenv("GROQ_API_KEY", "") else "missing",
    }
