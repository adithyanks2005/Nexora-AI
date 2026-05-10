from __future__ import annotations

from typing import AsyncIterator

from backend.ai import call_ai, SYSTEM_PROMPT


async def get_ai_reply(messages: list[dict]) -> str:
    """Single-shot reply from the configured Gemini model."""
    return await call_ai(messages, SYSTEM_PROMPT)


async def stream_ai_reply(messages: list[dict]) -> AsyncIterator[str]:
    """Compatibility stream helper; yields the Gemini reply as one chunk."""
    yield await get_ai_reply(messages)


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
