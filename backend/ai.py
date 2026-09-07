from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
import httpx
from fastapi import HTTPException

# Load .env if it exists
_dotenv = Path(__file__).resolve().parents[1] / ".env"
if _dotenv.exists():
    load_dotenv(_dotenv, override=True)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
MODEL_FALLBACKS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]
MAX_HISTORY_MESSAGES = 10
MAX_MESSAGE_CHARS = 1100

# Persistent client with separate connect/read timeouts for streaming.
_http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(60.0, connect=10.0),
    http2=True,
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
)

SYSTEM_PROMPT = """You are Nexora AI, a clinical medical AI companion. Provide accurate, high-quality medical insights, symptom analysis, and medication suggestions as concisely as possible.

RULES:
0. Health & medical queries only.
1. Use conversation context when available.
2. Suggest relevant OTC/generic medications with typical dosage and safety disclaimers.
3. Structure:
   - **Analysis & Context**: Brief explanation based on symptoms/history.
   - **Medications & Care**: Clear bullet points (OTC drugs, doses, home care).
   - **Red Flags**: Brief warning signs to see a doctor.
4. Give complete, well-formatted answers, normally 250–350 words when needed. Always finish every section and sentence. Never stop mid-sentence or mid-bullet. Prioritize red flags and essential care advice if space is limited.
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
    "article", "hygiene", "pill", "tablet", "syrup", "ointment"
}


def _is_health_query(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return True
    if re.fullmatch(r"(hi|hello|hey|hii+|good (morning|afternoon|evening)|yo)\W*", t):
        return True
    return any(k in t for k in HEALTH_KEYWORDS)


def _prepare_messages(messages: list[dict], system: str) -> list[dict]:
    """Keep requests small enough for Groq rate/token limits while preserving recent context."""
    cleaned = []
    for msg in messages[-MAX_HISTORY_MESSAGES:]:
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        cleaned.append({
            "role": msg.get("role", "user"),
            "content": content[-MAX_MESSAGE_CHARS:],
        })
    return [{"role": "system", "content": system}] + cleaned


MEDICATION_DISCLAIMER = (
    "\n\n> ⚠️ **Medication disclaimer:** Medication information is for educational purposes only. "
    "Do not start, stop, or change any medicine or dose without advice from a qualified "
    "healthcare professional. Check allergies, pregnancy, age, existing conditions, and "
    "possible drug interactions with a doctor or pharmacist."
)


def _contains_medication_advice(text: str) -> bool:
    lowered = (text or "").lower()
    medication_terms = (
        "medication", "medicine", "tablet", "capsule", "syrup", "spray", "ointment",
        "dose", "dosage", "mg", "mcg", "ml", "paracetamol", "acetaminophen", "ibuprofen",
        "antibiotic", "antihistamine", "saline nasal spray", "oral rehydration",
        "take twice", "take once", "per day", "every ", "after meals", "before meals"
    )
    return any(term in lowered for term in medication_terms)


def _ensure_medication_disclaimer(text: str) -> str:
    if not text or "Medication disclaimer:" in text:
        return text
    return text + MEDICATION_DISCLAIMER if _contains_medication_advice(text) else text


def _groq_error(status_code: int, body: str) -> str:
    try:
        data = json.loads(body)
        message = data.get("error", {}).get("message", "")
    except (json.JSONDecodeError, TypeError):
        message = ""

    if status_code == 401:
        return "AI service authentication failed. Check the GROQ_API_KEY configured in Vercel."
    if status_code == 403:
        return "AI service access was denied. Check Groq project/model permissions."
    if status_code == 404:
        return f"AI model is unavailable for this Groq key. Requested model: {message or 'not available'}"
    if status_code == 429:
        return "AI service rate limit reached. Please wait a moment and try again."
    if status_code == 400:
        return f"AI request was rejected: {message or 'invalid request'}"
    if status_code >= 500:
        return "AI service is temporarily unavailable. Please try again shortly."
    return f"AI service returned HTTP {status_code}."


async def _discover_available_model(api_key: str, preferred: str) -> str | None:
    """Ask Groq which models this API key can actually access and pick a supported fallback."""
    try:
        resp = await _http_client.get(
            GROQ_MODELS_URL,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        available = {
            str(item.get("id"))
            for item in data.get("data", [])
            if item.get("id")
        }
        if preferred in available:
            return preferred
        for candidate in MODEL_FALLBACKS:
            if candidate in available:
                return candidate
        # Prefer any currently active Llama/GPT production model if the key exposes one.
        for model_id in sorted(available):
            if any(prefix in model_id for prefix in ("llama-", "openai/gpt-oss-")):
                return model_id
        return None
    except (httpx.HTTPError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"WARN: Could not discover Groq models: {exc}")
        return None


async def _post_chat(api_key: str, model: str, payload: dict, headers: dict) -> httpx.Response:
    payload = dict(payload)
    payload["model"] = model
    return await _http_client.post(GROQ_URL, json=payload, headers=headers)


async def call_ai(messages: list[dict], system: str = SYSTEM_PROMPT) -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    configured_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not configured. 🛠️ LOCAL: Add it to your .env file and restart. 🚀 VERCEL: Add it to Project Settings > Environment Variables."
        )

    last_user_msg = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    if not _is_health_query(last_user_msg):
        return (
            "I am specialized exclusively in health and medical topics. "
            "Please ask a health-related question, symptom, or wellness concern."
        )

    payload = {
        "model": configured_model,
        "messages": _prepare_messages(messages, system),
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 900,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }

    try:
        resp = await _post_chat(api_key, configured_model, payload, headers)
    except httpx.TimeoutException as e:
        print(f"ERROR: Groq request timed out: {e}")
        raise HTTPException(status_code=504, detail="AI service timed out. Please try again.")
    except httpx.HTTPError as e:
        print(f"ERROR: Groq request failed: {e}")
        raise HTTPException(status_code=503, detail="Failed to connect to AI service. Please try again.")

    if resp.status_code == 404:
        discovered = await _discover_available_model(api_key, configured_model)
        if discovered and discovered != configured_model:
            print(f"INFO: Groq model {configured_model!r} unavailable; retrying with {discovered!r}")
            try:
                resp = await _post_chat(api_key, discovered, payload, headers)
            except httpx.HTTPError as e:
                print(f"ERROR: Groq fallback request failed: {e}")
                raise HTTPException(status_code=503, detail="Failed to connect to AI service. Please try again.")

    if resp.status_code != 200:
        print(f"ERROR: Groq returned {resp.status_code}: {resp.text}")
        raise HTTPException(status_code=resp.status_code, detail=_groq_error(resp.status_code, resp.text))

    data = resp.json()
    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    if not reply:
        print("ERROR: Groq returned empty response")
        raise HTTPException(status_code=502, detail="Groq returned an empty response. Please try again.")
    return _ensure_medication_disclaimer(reply)


async def stream_ai(messages: list[dict], system: str = SYSTEM_PROMPT) -> AsyncGenerator[str, None]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    configured_model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL

    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured.")

    last_user_msg = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    if not _is_health_query(last_user_msg):
        yield (
            "I am specialized exclusively in health and medical topics. "
            "Please ask a health-related question, symptom, or wellness concern."
        )
        return

    base_payload = {
        "model": configured_model,
        "messages": _prepare_messages(messages, system),
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 900,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "content-type": "application/json",
        "accept": "text/event-stream",
    }

    collected: list[str] = []

    for attempt in range(2):
        try:
            async with _http_client.stream(
                "POST",
                GROQ_URL,
                json={**base_payload, "model": configured_model},
                headers=headers,
            ) as response:
                if response.status_code == 404 and attempt == 0:
                    discovered = await _discover_available_model(api_key, configured_model)
                    if discovered and discovered != configured_model:
                        print(f"INFO: Groq streaming model {configured_model!r} unavailable; retrying with {discovered!r}")
                        configured_model = discovered
                        continue

                if response.status_code != 200:
                    text = (await response.aread()).decode("utf-8", errors="replace")
                    print(f"ERROR: Groq streaming returned {response.status_code}: {text}")
                    if attempt == 0 and response.status_code in {429, 500, 502, 503, 504}:
                        await asyncio.sleep(1.2)
                        continue
                    yield _groq_error(response.status_code, text)
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        collected.append(content)
                        yield content
                if collected:
                    full_text = "".join(collected)
                    if _contains_medication_advice(full_text) and "Medication disclaimer:" not in full_text:
                        yield MEDICATION_DISCLAIMER
                return
        except httpx.TimeoutException as e:
            print(f"ERROR: Groq streaming timed out: {e}")
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            yield "AI service timed out. Please try again."
            return
        except httpx.HTTPError as e:
            print(f"ERROR: Groq streaming failed: {e}")
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            yield "Unable to connect to the AI service. Please try again."
            return


def get_ai_status() -> dict[str, str]:
    return {
        "provider": "groq",
        "model": os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        "api_key": "configured" if os.getenv("GROQ_API_KEY", "") else "missing",
    }


def _extract_json(text: str):
    if not text:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


CLINICAL_QUESTIONS_PROMPT = """You are Ada Health's Clinical Diagnostic Engine.
Given a patient's symptoms, demographics, and risk factors, generate 3 to 5 crucial, discriminative clinical follow-up questions to rule in or out potential medical conditions.
Each question should be simple, empathetic, and offer choices: ["Yes", "No", "Not sure"].

OUTPUT FORMAT: Strict JSON only. No markdown, no conversation.
{
  "questions": [
    {
      "id": "q1",
      "question": "Did your symptom begin suddenly within seconds or minutes?",
      "options": ["Yes", "No", "Not sure"],
      "category": "onset"
    }
  ]
}
"""


def _fallback_clinical_questions(symptoms: list[str], body_area: str) -> list[dict]:
    sym_lower = " ".join(symptoms).lower()
    questions = []

    # Onset / Acuteness
    questions.append({
        "id": "q_onset",
        "question": "Did your symptoms begin suddenly (within minutes to hours) rather than gradually over days?",
        "options": ["Yes", "No", "Not sure"],
        "category": "onset"
    })

    if any(k in sym_lower for k in ["headache", "head", "migraine"]):
        questions.append({
            "id": "q_light",
            "question": "Are your symptoms accompanied by unusual sensitivity to bright light, sound, or nausea?",
            "options": ["Yes", "No", "Not sure"],
            "category": "characteristics"
        })
        questions.append({
            "id": "q_neck",
            "question": "Do you experience neck stiffness, difficulty bringing your chin to your chest, or a fever?",
            "options": ["Yes", "No", "Not sure"],
            "category": "red_flag"
        })
    elif any(k in sym_lower for k in ["chest", "heart", "breath", "shortness"]):
        questions.append({
            "id": "q_radiate",
            "question": "Does any discomfort radiate to your left arm, shoulder, jaw, neck, or back?",
            "options": ["Yes", "No", "Not sure"],
            "category": "red_flag"
        })
        questions.append({
            "id": "q_exertion",
            "question": "Does the discomfort worsen with physical exertion and improve when resting?",
            "options": ["Yes", "No", "Not sure"],
            "category": "characteristics"
        })
    elif any(k in sym_lower for k in ["cough", "fever", "throat", "cold", "flu"]):
        questions.append({
            "id": "q_fever_temp",
            "question": "Do you have a measured fever above 38.5°C (101.3°F) or persistent chills?",
            "options": ["Yes", "No", "Not sure"],
            "category": "severity"
        })
        questions.append({
            "id": "q_breath",
            "question": "Are you experiencing any shortness of breath, wheezing, or difficulty speaking full sentences?",
            "options": ["Yes", "No", "Not sure"],
            "category": "red_flag"
        })
    elif any(k in sym_lower for k in ["stomach", "abdomen", "nausea", "vomit", "diarrhea"]):
        questions.append({
            "id": "q_sharp",
            "question": "Is the abdominal pain sharp and localized to one specific spot (such as the lower right side)?",
            "options": ["Yes", "No", "Not sure"],
            "category": "characteristics"
        })
        questions.append({
            "id": "q_hydration",
            "question": "Have you been unable to keep liquids down for more than 12 hours, or feel severely dizzy?",
            "options": ["Yes", "No", "Not sure"],
            "category": "red_flag"
        })
    else:
        questions.append({
            "id": "q_fever",
            "question": "Do you currently have a fever, body chills, or nighttime sweats?",
            "options": ["Yes", "No", "Not sure"],
            "category": "associated"
        })
        questions.append({
            "id": "q_interference",
            "question": "Are these symptoms significantly disrupting your normal sleep, appetite, or daily activities?",
            "options": ["Yes", "No", "Not sure"],
            "category": "severity"
        })

    questions.append({
        "id": "q_worsening",
        "question": "Have your symptoms progressively worsened since they first started?",
        "options": ["Yes", "No", "Not sure"],
        "category": "progression"
    })
    return questions[:5]


async def generate_clinical_questions(data: dict) -> list[dict]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    symptoms = data.get("symptoms", [])
    body_area = data.get("body_area", "")
    age = data.get("age")
    gender = data.get("gender")
    risk_factors = data.get("risk_factors", [])

    if not api_key:
        return _fallback_clinical_questions(symptoms, body_area)

    user_prompt = (
        f"Patient Profile: Age {age or 'Not specified'}, Sex {gender or 'Not specified'}, "
        f"Risk factors: {', '.join(risk_factors) or 'None'}. "
        f"Primary Symptoms: {', '.join(symptoms)}. Body Area: {body_area or 'General'}. "
        f"Generate 3-5 discriminative follow-up diagnostic questions in JSON."
    )

    try:
        reply = await call_ai(
            [{"role": "user", "content": user_prompt}],
            system=CLINICAL_QUESTIONS_PROMPT,
        )
        parsed = _extract_json(reply)
        if isinstance(parsed, dict) and "questions" in parsed and isinstance(parsed["questions"], list):
            valid = []
            for i, q in enumerate(parsed["questions"][:5]):
                if isinstance(q, dict) and "question" in q:
                    valid.append({
                        "id": q.get("id") or f"q_{i+1}",
                        "question": q["question"],
                        "options": q.get("options") or ["Yes", "No", "Not sure"],
                        "category": q.get("category", "general"),
                    })
            if valid:
                return valid
    except Exception as exc:
        print(f"WARN: Failed generating clinical questions via AI: {exc}")

    return _fallback_clinical_questions(symptoms, body_area)


CLINICAL_ASSESSMENT_PROMPT = """You are Ada Health's Clinical Diagnostic & Medical Triage Engine.
Perform an evidence-based differential diagnosis and patient triage assessment.

Output strict JSON only matching this schema:
{
  "triage_level": "emergency" | "urgent_care" | "routine_doctor" | "self_care",
  "triage_title": "Headline recommendation (e.g. Urgent Care Evaluation Recommended)",
  "triage_description": "2-3 clear sentences explaining why this urgency was selected.",
  "primary_condition": "Name of top differential diagnosis",
  "conditions": [
    {
      "name": "Condition name",
      "probability": 85,
      "urgency": "critical" | "high" | "medium" | "low",
      "summary": "Clear, patient-friendly description of what this condition is.",
      "common_symptoms": ["List of 2-4 classic symptoms"],
      "matching_symptoms": ["Symptoms present in this patient"],
      "absent_symptoms": ["Classic symptoms patient does not exhibit"],
      "when_to_see_doctor": "Specific trigger for seeking medical care"
    }
  ],
  "emergency_warnings": ["Warning sign 1", "Warning sign 2"],
  "questions_for_doctor": ["Questions for doctor consultation"],
  "self_care_advice": ["Evidence-based safe self-care and home comfort measures"],
  "disclaimer": "This assessment is powered by clinical AI models for informational purposes only. It is not a medical diagnosis or treatment plan. If experiencing a life-threatening emergency, call emergency services immediately."
}
"""


def _fallback_clinical_assessment(data: dict) -> dict:
    symptoms = data.get("symptoms", [])
    sym_lower = " ".join(symptoms).lower()
    severity = (data.get("severity") or "").lower()
    area = data.get("body_area") or "General"
    age = data.get("age") or "Adult"
    answers = {a.get("id"): a.get("answer") for a in data.get("answers", [])}

    # Detect emergency indicators
    is_emergency = (
        severity == "severe" and any(k in sym_lower for k in ["chest", "breath", "faint", "numbness", "paralysis"])
    ) or answers.get("q_radiate") == "Yes" or answers.get("q_neck") == "Yes"

    if is_emergency:
        triage_level = "emergency"
        triage_title = "Immediate Medical Attention Recommended"
        triage_desc = (
            "Based on the critical combination of reported symptoms and severity, "
            "immediate evaluation by emergency medical services is strongly advised."
        )
    elif severity == "severe" or answers.get("q_fever_temp") == "Yes" or answers.get("q_sharp") == "Yes":
        triage_level = "urgent_care"
        triage_title = "Urgent Medical Care Advised (Within 24 Hours)"
        triage_desc = (
            "Your symptoms indicate an acute issue that warrants prompt evaluation "
            "by a healthcare provider at an urgent care clinic or primary physician."
        )
    elif severity == "moderate":
        triage_level = "routine_doctor"
        triage_title = "Doctor Consultation Recommended"
        triage_desc = (
            "Your symptoms are moderate and persistent. Scheduling a standard appointment "
            "with your primary care doctor will help determine the underlying cause."
        )
    else:
        triage_level = "self_care"
        triage_title = "Self-Care & Home Monitoring"
        triage_desc = (
            "Your current symptoms appear mild. Supportive home care and monitoring "
            "are typically sufficient, but seek medical evaluation if symptoms worsen."
        )

    # Differential conditions
    conditions = []
    if any(k in sym_lower for k in ["headache", "head"]):
        conditions.append({
            "name": "Tension-Type Headache",
            "probability": 75,
            "urgency": "low",
            "summary": "A common type of headache causing diffuse, mild-to-moderate band-like pain.",
            "common_symptoms": ["Dull aching head pain", "Sensation of tightness", "Tenderness on scalp"],
            "matching_symptoms": [s for s in symptoms if "head" in s.lower() or "pain" in s.lower()],
            "absent_symptoms": ["Severe nausea", "Visual aura", "Fever"],
            "when_to_see_doctor": "If headaches become frequent, unusually severe, or disrupt daily life."
        })
        conditions.append({
            "name": "Migraine",
            "probability": 55,
            "urgency": "medium",
            "summary": "A neurological condition characterized by intense, throbbing unilateral or bilateral head pain.",
            "common_symptoms": ["Throbbing head pain", "Sensitivity to light/sound", "Nausea"],
            "matching_symptoms": [s for s in symptoms if "head" in s.lower()],
            "absent_symptoms": ["Sudden thunderclap onset"],
            "when_to_see_doctor": "If attacks occur multiple times per month or OTC remedies fail."
        })
    elif any(k in sym_lower for k in ["cough", "cold", "fever", "throat"]):
        conditions.append({
            "name": "Upper Respiratory Tract Infection (URTI)",
            "probability": 82,
            "urgency": "low",
            "summary": "Viral infection affecting the nose, throat, and airways such as the common cold.",
            "common_symptoms": ["Cough", "Sore throat", "Nasal congestion", "Low-grade fever"],
            "matching_symptoms": symptoms[:2],
            "absent_symptoms": ["Severe shortness of breath", "Chest pain"],
            "when_to_see_doctor": "If fever persists over 3 days or breathing becomes difficult."
        })
        conditions.append({
            "name": "Acute Bronchitis",
            "probability": 48,
            "urgency": "medium",
            "summary": "Inflammation of the bronchial tubes, often following a viral cold.",
            "common_symptoms": ["Persistent cough with mucus", "Chest soreness", "Fatigue"],
            "matching_symptoms": [s for s in symptoms if "cough" in s.lower()],
            "absent_symptoms": ["High continuous fever"],
            "when_to_see_doctor": "If cough lasts more than 3 weeks or produces blood."
        })
    else:
        primary_name = f"Acute {symptoms[0].title()} Presentation" if symptoms else "Symptom Syndrome"
        conditions.append({
            "name": primary_name,
            "probability": 70,
            "urgency": "medium" if severity != "severe" else "high",
            "summary": f"Clinical presentation involving {', '.join(symptoms)} in the {area} region.",
            "common_symptoms": symptoms,
            "matching_symptoms": symptoms,
            "absent_symptoms": ["Systemic collapse", "Uncontrolled hemorrhage"],
            "when_to_see_doctor": "If symptoms escalate in severity or do not improve with conservative care."
        })

    return {
        "triage_level": triage_level,
        "triage_title": triage_title,
        "triage_description": triage_desc,
        "primary_condition": conditions[0]["name"] if conditions else "Unspecified Presentation",
        "conditions": conditions,
        "emergency_warnings": [
            "Sudden severe shortness of breath or inability to catch breath",
            "Crushing chest pressure or pain spreading to jaw or arm",
            "Sudden confusion, speech difficulty, or weakness on one side of body",
            "Stiff neck accompanied by high fever and severe headache"
        ],
        "questions_for_doctor": [
            "What is the most likely cause of my specific symptom cluster?",
            "Are there any diagnostic tests (blood work, imaging) recommended?",
            "What red flag symptoms should prompt an immediate hospital visit?",
            "Are there specific lifestyle changes or OTC medications suitable for me?"
        ],
        "self_care_advice": [
            "Stay thoroughly hydrated with water and electrolyte-rich fluids.",
            "Prioritize physical rest and allow your body adequate recovery time.",
            "Monitor your temperature and symptom progression twice daily.",
            "Avoid intense physical exertion until symptoms resolve."
        ],
        "disclaimer": "This assessment is powered by clinical AI models for informational purposes only. It is not a medical diagnosis or treatment plan. If you are experiencing a life-threatening emergency, call emergency services immediately."
    }


async def generate_clinical_assessment(data: dict) -> dict:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    symptoms = data.get("symptoms", [])
    body_area = data.get("body_area", "")
    severity = data.get("severity", "")
    duration = data.get("duration", "")
    age = data.get("age")
    gender = data.get("gender")
    is_pregnant = data.get("is_pregnant", False)
    onset = data.get("onset", "")
    progression = data.get("progression", "")
    risk_factors = data.get("risk_factors", [])
    answers = data.get("answers", [])

    if not api_key:
        return _fallback_clinical_assessment(data)

    answers_str = "; ".join(f"{a.get('question', a.get('id'))}: {a.get('answer')}" for a in answers)
    user_prompt = (
        f"PATIENT DEMOGRAPHICS: Age {age or 'Unspecified'}, Sex {gender or 'Unspecified'}, Pregnant: {is_pregnant}. "
        f"MEDICAL RISK FACTORS: {', '.join(risk_factors) or 'None'}. "
        f"PRESENTING SYMPTOMS: {', '.join(symptoms)}. "
        f"BODY REGION: {body_area or 'General'}. "
        f"SEVERITY: {severity or 'Moderate'}. DURATION: {duration or 'Unspecified'}. "
        f"ONSET: {onset or 'Unspecified'}. PROGRESSION: {progression or 'Unspecified'}. "
        f"CLINICAL QUESTION RESPONSES: {answers_str or 'None'}. "
        "Formulate a complete Ada Health-grade clinical differential assessment and triage report in JSON."
    )

    try:
        reply = await call_ai(
            [{"role": "user", "content": user_prompt}],
            system=CLINICAL_ASSESSMENT_PROMPT,
        )
        parsed = _extract_json(reply)
        if isinstance(parsed, dict) and "triage_level" in parsed and "conditions" in parsed:
            # Validate required fields and normalize
            parsed.setdefault("emergency_warnings", [])
            parsed.setdefault("questions_for_doctor", [])
            parsed.setdefault("self_care_advice", [])
            parsed.setdefault("disclaimer", "This assessment is for informational purposes only.")
            return parsed
    except Exception as exc:
        print(f"WARN: AI clinical assessment failed, falling back: {exc}")

    return _fallback_clinical_assessment(data)

