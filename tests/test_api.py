"""
Nexora AI — API Tests
Run: pytest tests/ -v
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.database import USING_SUPABASE, create_chat_session, get_connection, init_db
from backend.main import app

# Initialise DB before any test runs
init_db()

client = TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    r = client.post("/api/auth/guest")
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


# ── Health check ──────────────────────────────────────────────────────────────
def test_health_endpoint():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_valid_jwt_recovers_missing_local_user_row():
    if USING_SUPABASE:
        pytest.skip("Local user-row recovery only applies to SQLite fallback storage.")

    r = client.post(
        "/api/auth/google",
        json={"id_token": "mock_google_recover@example.com", "workplace_id": "recover"},
    )
    assert r.status_code == 200
    data = r.json()
    headers = {"Authorization": f"Bearer {data['token']}"}

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM users WHERE id = ? AND workplace_id = ?",
            (data["user"]["id"], data["user"]["workplace_id"]),
        )

    recovered = client.get("/api/reminders", headers=headers)
    assert recovered.status_code == 200
    assert recovered.json() == []


# ── Sessions ──────────────────────────────────────────────────────────────────
def test_create_and_list_session(auth_headers):
    r = client.post("/api/sessions", json={"title": "Test Session"}, headers=auth_headers)
    assert r.status_code == 201
    sid = r.json()["id"]

    r2 = client.get("/api/sessions", headers=auth_headers)
    assert r2.status_code == 200
    ids = [s["id"] for s in r2.json()]
    assert sid in ids

    client.delete(f"/api/sessions/{sid}", headers=auth_headers)


def test_delete_session(auth_headers):
    r = client.post("/api/sessions", json={"title": "Delete Me"}, headers=auth_headers)
    sid = r.json()["id"]
    r2 = client.delete(f"/api/sessions/{sid}", headers=auth_headers)
    assert r2.status_code == 200


def test_chat_replaces_session_id_owned_by_another_user(monkeypatch):
    user_a = client.post("/api/auth/guest", headers={"X-Workplace-ID": "collision"}).json()["user"]
    user_b_login = client.post("/api/auth/guest", headers={"X-Workplace-ID": "collision"}).json()
    user_b_headers = {"Authorization": f"Bearer {user_b_login['token']}"}
    stale_session_id = str(uuid.uuid4())

    create_chat_session(stale_session_id, user_a["id"], user_a["workplace_id"], "Existing")

    async def fake_call_ai(messages):
        return "ok"

    monkeypatch.setattr("backend.main.call_ai", fake_call_ai)
    r = client.post(
        "/api/chat",
        json={
            "session_id": stale_session_id,
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers=user_b_headers,
    )

    assert r.status_code == 200
    assert r.json()["reply"] == "ok"
    assert r.json()["session_id"] != stale_session_id


# ── Calculators ───────────────────────────────────────────────────────────────
def test_bmi_normal():
    r = client.post("/api/calc/bmi", json={"weight": 70, "height": 175, "unit": "metric"})
    assert r.status_code == 200
    data = r.json()
    assert 18.5 <= data["bmi"] < 25
    assert data["category"] == "Normal Weight ✓"


def test_bmi_underweight():
    r = client.post("/api/calc/bmi", json={"weight": 45, "height": 175, "unit": "metric"})
    assert r.status_code == 200
    assert r.json()["category"] == "Underweight"


def test_bmi_overweight():
    r = client.post("/api/calc/bmi", json={"weight": 90, "height": 175, "unit": "metric"})
    assert r.status_code == 200
    assert r.json()["category"] == "Overweight"


def test_bmi_imperial():
    r = client.post("/api/calc/bmi", json={"weight": 154, "height": 175, "unit": "imperial"})
    assert r.status_code == 200
    assert "bmi" in r.json()


def test_calories_male_maintain():
    r = client.post("/api/calc/calories", json={
        "age": 30, "gender": "male", "weight": 75,
        "height": 175, "activity": 1.55, "goal": "maintain"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["tdee"] == data["target"]
    assert data["protein_g"] > 0


def test_calories_female_lose():
    r = client.post("/api/calc/calories", json={
        "age": 28, "gender": "female", "weight": 65,
        "height": 165, "activity": 1.375, "goal": "lose"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["target"] == data["tdee"] - 500


def test_water_basic():
    r = client.post("/api/calc/water", json={"weight": 70, "activity": 0, "climate": 0})
    assert r.status_code == 200
    data = r.json()
    assert data["litres"] > 0
    assert data["ml"] == round(data["litres"] * 1000)


def test_ideal_weight_male():
    r = client.post("/api/calc/ideal-weight", json={"height": 175, "gender": "male"})
    assert r.status_code == 200
    data = r.json()
    assert data["low"] < data["ideal"] < data["high"]


def test_ideal_weight_female():
    r = client.post("/api/calc/ideal-weight", json={"height": 165, "gender": "female"})
    assert r.status_code == 200
    assert "ideal" in r.json()


# ── Reminders ─────────────────────────────────────────────────────────────────
def test_reminder_crud(auth_headers):
    # Create
    r = client.post("/api/reminders", json={
        "title": "Test Vitamin", "time": "09:00",
        "repeat": "Daily", "notes": "With food", "icon": "💊", "color": "#E6F1FB"
    }, headers=auth_headers)
    assert r.status_code == 201
    rid = r.json()["id"]

    # List
    r2 = client.get("/api/reminders", headers=auth_headers)
    assert any(rem["id"] == rid for rem in r2.json())

    # Toggle
    r3 = client.patch(f"/api/reminders/{rid}/toggle", headers=auth_headers)
    assert r3.status_code == 200
    assert r3.json()["done"] == 1

    # Toggle back
    r4 = client.patch(f"/api/reminders/{rid}/toggle", headers=auth_headers)
    assert r4.json()["done"] == 0

    # Delete
    r5 = client.delete(f"/api/reminders/{rid}", headers=auth_headers)
    assert r5.status_code == 200


def test_reminder_not_found(auth_headers):
    r = client.patch("/api/reminders/999999/toggle", headers=auth_headers)
    assert r.status_code == 404


def test_clear_done_reminders(auth_headers):
    # Add and mark done
    r = client.post("/api/reminders", json={
        "title": "Done Reminder", "time": "10:00",
        "repeat": "Once", "notes": "", "icon": "✅", "color": "#E1F5EE"
    }, headers=auth_headers)
    rid = r.json()["id"]
    client.patch(f"/api/reminders/{rid}/toggle", headers=auth_headers)

    r2 = client.delete("/api/reminders/done/clear", headers=auth_headers)
    assert r2.status_code == 200

    remaining = client.get("/api/reminders", headers=auth_headers).json()
    assert all(rem["done"] == 0 for rem in remaining)


# ── Health Records ────────────────────────────────────────────────────────────
def test_health_record_crud(auth_headers):
    # Create
    r = client.post("/api/records", json={
        "type": "Blood Pressure", "data": "120/80 mmHg", "notes": "Morning reading"
    }, headers=auth_headers)
    assert r.status_code == 201
    rid = r.json()["id"]

    # List
    r2 = client.get("/api/records", headers=auth_headers)
    assert any(rec["id"] == rid for rec in r2.json())

    # Delete
    r3 = client.delete(f"/api/records/{rid}", headers=auth_headers)
    assert r3.status_code == 200


def test_health_record_types(auth_headers):
    types = ["Weight", "Heart Rate", "Blood Sugar", "Sleep", "Mood"]
    ids = []
    for t in types:
        r = client.post("/api/records", json={"type": t, "data": "test value", "notes": ""}, headers=auth_headers)
        assert r.status_code == 201
        ids.append(r.json()["id"])
    for rid in ids:
        client.delete(f"/api/records/{rid}", headers=auth_headers)
