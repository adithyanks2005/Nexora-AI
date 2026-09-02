from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    messages: list[Message] = Field(min_length=1, max_length=20)


class SessionCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=100)


class ReminderIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    time: str = Field(max_length=50)
    repeat: str = Field(default="Daily", max_length=50)
    notes: str = Field(default="", max_length=1000)
    icon: str = Field(default="💊", max_length=20)
    color: str = Field(default="#E6F1FB", max_length=20)


class HealthRecordIn(BaseModel):
    type: str = Field(min_length=1, max_length=100)
    data: str = Field(max_length=5000)
    notes: str = Field(default="", max_length=2000)


class BMIRequest(BaseModel):
    weight: float = Field(gt=0, le=500)
    height: float = Field(gt=0, le=300)
    unit: Literal["metric", "imperial"] = "metric"


class CalorieRequest(BaseModel):
    age: float = Field(gt=0, le=120)
    gender: Literal["male", "female"]
    weight: float = Field(gt=0, le=500)
    height: float = Field(gt=0, le=300)
    activity: float = Field(ge=0, le=10)
    goal: Literal["lose", "maintain", "gain"]


class WaterRequest(BaseModel):
    weight: float = Field(gt=0, le=500)
    activity: float = Field(default=0.0, ge=0, le=24)
    climate: float = Field(default=0.0, ge=0, le=60)


class IdealWeightRequest(BaseModel):
    height: float = Field(gt=0, le=300)
    gender: Literal["male", "female"]


class SymptomRequest(BaseModel):
    symptoms: list[str] = Field(min_length=1, max_length=20)
    body_area: str = Field(default="", max_length=200)
    severity: str = Field(default="", max_length=100)
    duration: str = Field(default="", max_length=100)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(min_length=20, max_length=10000)
    workplace_id: str = Field(default="default", max_length=100)


class SupabaseAuthRequest(BaseModel):
    access_token: str = Field(min_length=20, max_length=10000)
    workplace_id: str = Field(default="default", max_length=100)


class CrawlRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=2048, description="The full URL (http/https) of the page to crawl.")
    respect_robots: bool = Field(True, description="Whether to respect the target site's robots.txt rules.")


class CrawlHeading(BaseModel):
    level: str
    text: str


class CrawlLink(BaseModel):
    url: str
    text: str


class CrawlResponse(BaseModel):
    url: str
    status_code: int
    elapsed_ms: int
    crawled_at: str
    title: str
    description: str
    headings: list[CrawlHeading]
    links: list[CrawlLink]
    links_count: int
    text_preview: str
    has_json_ld: bool
