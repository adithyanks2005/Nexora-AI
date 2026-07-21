from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, HttpUrl


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


# ── Auth models ───────────────────────────────────────────────────────────────
class GoogleAuthRequest(BaseModel):
    id_token: str
    workplace_id: str = "default"


class SupabaseAuthRequest(BaseModel):
    access_token: str
    workplace_id: str = "default"


# ── Crawler models ────────────────────────────────────────────────────────────
class CrawlRequest(BaseModel):
    url: str = Field(..., description="The full URL (http/https) of the page to crawl.")
    respect_robots: bool = Field(True, description="Whether to respect the target site's robots.txt rules.")


class CrawlHeading(BaseModel):
    level: str
    text:  str


class CrawlLink(BaseModel):
    url:  str
    text: str


class CrawlResponse(BaseModel):
    url:          str
    status_code:  int
    elapsed_ms:   int
    crawled_at:   str
    title:        str
    description:  str
    headings:     list[CrawlHeading]
    links:        list[CrawlLink]
    links_count:  int
    text_preview: str
    has_json_ld:  bool
