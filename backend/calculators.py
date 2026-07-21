from __future__ import annotations
from typing import Any
from fastapi import HTTPException
from backend.models import BMIRequest, CalorieRequest, WaterRequest, IdealWeightRequest


def calc_bmi(req: BMIRequest) -> dict[str, Any]:
    w, h = req.weight, req.height
    if req.unit == "imperial":
        w = w * 0.453592  # lbs to kg
        h = h * 0.0254    # inches to meters (NOT cm!)
        # Convert back to cm for the rest of the calculation
        h = h * 100       # meters to cm
    bmi = round(w / ((h / 100) ** 2), 1)
    if bmi < 18.5:
        cat, col, adv = "Underweight", "#378ADD", "Consider a calorie-rich, nutrient-dense diet. A dietitian can help."
        pct = max(4, (bmi / 18.5) * 22)
    elif bmi < 25:
        cat, col, adv = "Normal Weight ✓", "#1D9E75", "Great! Maintain with balanced diet and regular exercise."
        pct = 22 + ((bmi - 18.5) / 6.5) * 26
    elif bmi < 30:
        cat, col, adv = "Overweight", "#BA7517", "Gradual dietary changes and more activity can help. Even 5–10% loss brings big benefits."
        pct = 48 + ((bmi - 25) / 5) * 22
    else:
        cat, col, adv = "Obese", "#E24B4A", "Please consult a healthcare provider for a personalised weight management plan."
        pct = min(93, 70 + ((bmi - 30) / 10) * 23)
    return {"bmi": bmi, "category": cat, "color": col, "advice": adv, "needle_pct": round(pct)}


def calc_calories(req: CalorieRequest) -> dict[str, Any]:
    if req.gender == "male":
        bmr = 10 * req.weight + 6.25 * req.height - 5 * req.age + 5
    else:
        bmr = 10 * req.weight + 6.25 * req.height - 5 * req.age - 161
    tdee = round(bmr * req.activity)
    target = tdee - 500 if req.goal == "lose" else tdee + 500 if req.goal == "gain" else tdee
    return {
        "bmr":       round(bmr),
        "tdee":      tdee,
        "target":    target,
        "protein_g": round(req.weight * 1.6),
        "carbs_g":   round(target * 0.45 / 4),
        "fat_g":     round(target * 0.30 / 9),
    }


def calc_water(req: WaterRequest) -> dict[str, Any]:
    total = round((req.weight * 0.033 + req.activity + req.climate) * 10) / 10
    return {"litres": total, "cups": round(total / 0.237), "ml": round(total * 1000)}


def calc_ideal_weight(req: IdealWeightRequest) -> dict[str, Any]:
    # Devine formula is only valid for heights >= 152.4 cm (5 feet)
    if req.height < 152.4:
        raise HTTPException(
            status_code=400,
            detail=f"The Devine formula is only valid for heights >= 152.4 cm. Your height: {req.height} cm."
        )
    h_in  = (req.height - 152.4) / 2.54
    base  = 50 if req.gender == "male" else 45.5
    ideal = round((base + h_in * 2.3) * 10) / 10
    return {
        "low":       round((ideal - 5) * 10) / 10,
        "ideal":     ideal,
        "high":      round((ideal + 5) * 10) / 10,
        "gender":    req.gender,
        "height_cm": req.height,
    }
