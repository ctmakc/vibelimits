from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import EventType


@dataclass(slots=True)
class Classification:
    relevant: bool
    event_type: EventType | None
    confidence: float
    summary: str


RESET_PATTERNS = [
    r"\b(reset|resetting|resets|refill|refilled|restored)\b.{0,80}\b(limit|limits|quota|quotas|usage|credits?)\b",
    r"\b(limit|limits|quota|quotas|usage|credits?)\b.{0,80}\b(reset|resetting|resets|refill|refilled|restored)\b",
    r"\b100%\b.{0,50}\b(quota|usage|limit)\b",
]
INCREASE_PATTERNS = [r"\b(increas|rais|doubl|2x|3x|5x|10x|20x).{0,80}\b(limit|quota|usage|credits?)", r"\bmore usage\b"]
DECREASE_PATTERNS = [r"\b(reduc|lower|decreas|cut).{0,80}\b(limit|quota|usage|credits?)"]
PROMO_PATTERNS = [r"\b(bonus|promo|promotional|extra).{0,60}\b(reset|credit|usage|quota)", r"\bbanked reset\b"]
COMP_PATTERNS = [r"\b(compensat|make.?good|outage).{0,100}\b(credit|reset|quota|usage)"]
POLICY_PATTERNS = [r"\b(limit|limits|quota|quotas|usage).{0,100}\b(change|changing|new|update|billing cycle|window)"]


def _match(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, flags=re.I | re.S) for p in patterns)


def classify_rules(text: str) -> Classification:
    compact = " ".join(text.split())
    if _match(COMP_PATTERNS, compact):
        return Classification(True, EventType.OUTAGE_COMPENSATION, 0.86, compact[:500])
    if _match(PROMO_PATTERNS, compact):
        return Classification(True, EventType.PROMO_CREDIT, 0.84, compact[:500])
    if _match(RESET_PATTERNS, compact):
        return Classification(True, EventType.QUOTA_RESET, 0.90, compact[:500])
    if _match(INCREASE_PATTERNS, compact):
        return Classification(True, EventType.QUOTA_INCREASE, 0.86, compact[:500])
    if _match(DECREASE_PATTERNS, compact):
        return Classification(True, EventType.QUOTA_DECREASE, 0.86, compact[:500])
    if _match(POLICY_PATTERNS, compact):
        return Classification(True, EventType.POLICY_CHANGE, 0.72, compact[:500])
    return Classification(False, None, 0.0, "")


async def classify(text: str) -> Classification:
    return classify_rules(text)
