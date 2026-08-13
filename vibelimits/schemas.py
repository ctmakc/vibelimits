from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .providers import provider_ids


class EventType(StrEnum):
    QUOTA_RESET = "quota_reset"
    QUOTA_INCREASE = "quota_increase"
    QUOTA_DECREASE = "quota_decrease"
    POLICY_CHANGE = "policy_change"
    PROMO_CREDIT = "promo_credit"
    OUTAGE_COMPENSATION = "outage_compensation"
    PERSONAL_RESET = "personal_reset"


class Confidence(StrEnum):
    DETECTED = "detected"
    CONFIRMED = "confirmed"
    OFFICIAL = "official"


class QuotaWindow(BaseModel):
    name: str
    used_percent: float = Field(ge=0, le=100)
    reset_at: datetime | None = None
    window_minutes: int | None = None
    limit_total: float | None = None
    limit_remaining: float | None = None

    @field_validator("reset_at")
    @classmethod
    def ensure_tz(cls, value: datetime | None) -> datetime | None:
        if value and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class SensorReport(BaseModel):
    sensor_id: str = Field(min_length=8, max_length=128)
    provider: str
    account_hash: str = Field(min_length=8, max_length=128)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    windows: list[QuotaWindow] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider")
    @classmethod
    def known_provider(cls, value: str) -> str:
        if value not in provider_ids():
            raise ValueError(f"unknown provider: {value}")
        return value


class Announcement(BaseModel):
    provider: str
    source: str
    source_ref: str
    text: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    url: str | None = None
    official: bool = True


class EventOut(BaseModel):
    id: str
    provider: str
    event_type: str
    confidence: str
    title: str
    summary: str
    occurred_at: datetime
    evidence_count: int
    source_url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
