from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str
    messages: list[Message]


class SessionCreate(BaseModel):
    title: str = "New Chat"


class ReminderIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    time:  str
    repeat: str = "Daily"
    notes: str = ""
    icon:  str = "💊"
    color: str = "#E6F1FB"


class HealthRecordIn(BaseModel):
    type:  str
    data:  str
    notes: str = ""


class BMIRequest(BaseModel):
    weight: float
    height: float
    unit: Literal["metric", "imperial"] = "metric"


class CalorieRequest(BaseModel):
    age:      float
    gender:   Literal["male", "female"]
    weight:   float
    height:   float
    activity: float
    goal:     Literal["lose", "maintain", "gain"]


class WaterRequest(BaseModel):
    weight:   float
    activity: float = 0.0
    climate:  float = 0.0


class IdealWeightRequest(BaseModel):
    height: float
    gender: Literal["male", "female"]


class SymptomRequest(BaseModel):
    symptoms:  list[str]
    body_area: str = ""
    severity:  str = ""
    duration:  str = ""
