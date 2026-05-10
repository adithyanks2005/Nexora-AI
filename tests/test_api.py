"""
Nexora AI — API Tests
Run: pytest tests/ -v
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.database import init_db
from backend.main import app

# Initialise DB before any test runs
init_db()

client = TestClient(app)


# ── Health check ──────────────────────────────────────────────────────────────
def test_health_endpoint():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Sessions ──────────────────────────────────────────────────────────────────
def test_create_and_list_session():
    r = client.post("/api/sessions", json={"title": "Test Session"})
    assert r.status_code == 201
    sid = r.json()["id"]

    r2 = client.get("/api/sessions")
    assert r2.status_code == 200
    ids = [s["id"] for s in r2.json()]
    assert sid in ids

    client.delete(f"/api/sessions/{sid}")


def test_delete_session():
    r = client.post("/api/sessions", json={"title": "Delete Me"})
    sid = r.json()["id"]
    r2 = client.delete(f"/api/sessions/{sid}")
    assert r2.status_code == 200


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
def test_reminder_crud():
    # Create
    r = client.post("/api/reminders", json={
        "title": "Test Vitamin", "time": "09:00",
        "repeat": "Daily", "notes": "With food", "icon": "💊", "color": "#E6F1FB"
    })
    assert r.status_code == 201
    rid = r.json()["id"]

    # List
    r2 = client.get("/api/reminders")
    assert any(rem["id"] == rid for rem in r2.json())

    # Toggle
    r3 = client.patch(f"/api/reminders/{rid}/toggle")
    assert r3.status_code == 200
    assert r3.json()["done"] == 1

    # Toggle back
    r4 = client.patch(f"/api/reminders/{rid}/toggle")
    assert r4.json()["done"] == 0

    # Delete
    r5 = client.delete(f"/api/reminders/{rid}")
    assert r5.status_code == 200


def test_reminder_not_found():
    r = client.patch("/api/reminders/999999/toggle")
    assert r.status_code == 404


def test_clear_done_reminders():
    # Add and mark done
    r = client.post("/api/reminders", json={
        "title": "Done Reminder", "time": "10:00",
        "repeat": "Once", "notes": "", "icon": "✅", "color": "#E1F5EE"
    })
    rid = r.json()["id"]
    client.patch(f"/api/reminders/{rid}/toggle")

    r2 = client.delete("/api/reminders/done/clear")
    assert r2.status_code == 200

    remaining = client.get("/api/reminders").json()
    assert all(rem["done"] == 0 for rem in remaining)


# ── Health Records ────────────────────────────────────────────────────────────
def test_health_record_crud():
    # Create
    r = client.post("/api/records", json={
        "type": "Blood Pressure", "data": "120/80 mmHg", "notes": "Morning reading"
    })
    assert r.status_code == 201
    rid = r.json()["id"]

    # List
    r2 = client.get("/api/records")
    assert any(rec["id"] == rid for rec in r2.json())

    # Delete
    r3 = client.delete(f"/api/records/{rid}")
    assert r3.status_code == 200


def test_health_record_types():
    types = ["Weight", "Heart Rate", "Blood Sugar", "Sleep", "Mood"]
    ids = []
    for t in types:
        r = client.post("/api/records", json={"type": t, "data": "test value", "notes": ""})
        assert r.status_code == 201
        ids.append(r.json()["id"])
    for rid in ids:
        client.delete(f"/api/records/{rid}")
