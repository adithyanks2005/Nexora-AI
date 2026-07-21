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

SYSTEM_PROMPT = """You are Nexora AI, an advanced, highly knowledgeable clinical AI medical assistant. Your primary goal is to provide accurate, well-structured, and comprehensive medical insights, symptom analysis, treatment recommendations, and medication guidance based on user inquiries.

CRITICAL RULES - follow these strictly:
0. SCOPE: You are strictly specialized in health, medicine, pharmacology, symptoms, and wellness. Briefly decline non-medical questions and prompt for a health-related query.
1. CONTEXT: Always maintain continuity by analyzing previous messages in the conversation. Explicitly reference prior symptoms, medications, or user context when available.
2. MEDICAL & MEDICATION SUGGESTIONS:
   - Provide concrete medical responses, likely clinical explanations, and evidence-based self-care.
   - Suggest relevant Over-The-Counter (OTC) or standard prescription medications (including generic names, typical dosage ranges, and purpose).
   - Always include a brief disclaimer: *"Consult a licensed physician before starting or changing any medication."*
3. STRUCTURE & FORMATTING:
   - Use clean Markdown with clear headings and concise bullet points.
   - Structure your response using these sections:
     - **Context & Symptom Overview** (Brief synthesis & context from chat history)
     - **Potential Causes / Clinical Analysis**
     - **Suggested Medications & Self-Care** (Name OTC/medications, dosage notes, home remedies)
     - **Warning Signs & Medical Consultation** (Red flags requiring urgent care)
4. TONE & CLARITY: Maintain an empathetic, professional, and precise clinical tone. Avoid overly verbose explanations while ensuring thoroughness.

Example Response Format:
**Context & Overview:** I see from our earlier conversation that your tension headache has persisted...
**Potential Causes:** Muscle contraction, stress, mild dehydration.
**Suggested Medications & Remedies:**
- *Ibuprofen (Advil/Motrin):* 200–400mg every 4-6 hours with food for pain relief.
- *Hydration & Rest:* Drink at least 500ml water and rest in a dimmed room.
**When to Seek Care:** If accompanied by sudden severe pain, vision changes, or fever.
*(Disclaimer: Consult a medical professional before taking new medications.)*
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
    "article", "sleep", "hygiene", "pill", "tablet", "syrup", "ointment"
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
            "I am specialized exclusively in health and medical topics. "
            "Please ask a health-related question, symptom, or wellness concern."
        )

    payload = {
        "model": model,
        "messages": chat_messages,
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 650,
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
