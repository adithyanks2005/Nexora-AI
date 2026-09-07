"""
Ada Health-grade Clinical Symptom Checker API Tests
Run: pytest tests/test_symptoms_ada.py -v
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.database import init_db
from backend.main import app

init_db()
client = TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    r = client.post("/api/auth/guest")
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_clinical_questions_endpoint(auth_headers):
    payload = {
        "symptoms": ["Headache", "Nausea"],
        "body_area": "Head & Neck",
        "severity": "Moderate",
        "duration": "1-3 days",
        "age": 28,
        "gender": "female",
        "is_pregnant": False,
        "risk_factors": ["High Stress / Anxiety"]
    }
    r = client.post("/api/symptoms/questions", json=payload, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "questions" in data
    assert len(data["questions"]) >= 2
    for q in data["questions"]:
        assert "id" in q
        assert "question" in q
        assert "options" in q
        assert len(q["options"]) >= 2


def test_clinical_assessment_endpoint(auth_headers):
    payload = {
        "symptoms": ["Cough", "Sore throat", "Fever"],
        "body_area": "Chest",
        "severity": "Mild",
        "duration": "1-3 days",
        "age": 32,
        "gender": "male",
        "is_pregnant": False,
        "onset": "Gradual",
        "progression": "Constant",
        "risk_factors": ["Smoker"],
        "answers": [
            {"id": "q_onset", "question": "Did symptoms begin suddenly?", "answer": "No"},
            {"id": "q_fever_temp", "question": "Do you have high fever?", "answer": "No"}
        ]
    }
    r = client.post("/api/symptoms/assess", json=payload, headers=auth_headers)
    assert r.status_code == 200
    report = r.json()
    assert "triage_level" in report
    assert report["triage_level"] in ["emergency", "urgent_care", "routine_doctor", "self_care"]
    assert "triage_title" in report
    assert "triage_description" in report
    assert "conditions" in report
    assert len(report["conditions"]) > 0
    cond = report["conditions"][0]
    assert "name" in cond
    assert "probability" in cond
    assert 0 <= cond["probability"] <= 100
    assert "questions_for_doctor" in report
    assert "self_care_advice" in report


def test_clinical_assessment_emergency_triage(auth_headers):
    payload = {
        "symptoms": ["Severe chest pain", "Shortness of breath"],
        "body_area": "Chest",
        "severity": "Severe",
        "duration": "Less than 1 day",
        "age": 55,
        "gender": "male",
        "risk_factors": ["High Blood Pressure", "Heart Condition"],
        "answers": [
            {"id": "q_radiate", "question": "Does pain radiate to arm or jaw?", "answer": "Yes"}
        ]
    }
    r = client.post("/api/symptoms/assess", json=payload, headers=auth_headers)
    assert r.status_code == 200
    report = r.json()
    assert report["triage_level"] == "emergency"
    assert "Immediate" in report["triage_title"] or "Emergency" in report["triage_title"]


def test_legacy_symptoms_endpoint_compatibility(auth_headers):
    payload = {
        "symptoms": ["Fatigue", "Dizziness"],
        "body_area": "General / Whole body",
        "severity": "Mild",
        "duration": "4-7 days"
    }
    r = client.post("/api/symptoms", json=payload, headers=auth_headers)
    assert r.status_code == 200
    assert "reply" in r.json()
