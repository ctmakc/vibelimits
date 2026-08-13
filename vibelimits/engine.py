from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Iterable

from .classifier import classify
from .config import settings
from .providers import PROVIDERS
from .schemas import Announcement, Confidence, EventType, QuotaWindow, SensorReport
from .state import EventRecord, StateStore, store


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _window_dict(w: QuotaWindow) -> dict:
    return {
        "name": w.name,
        "used_percent": w.used_percent,
        "reset_at": w.reset_at.isoformat() if w.reset_at else None,
        "window_minutes": w.window_minutes,
        "limit_total": w.limit_total,
        "limit_remaining": w.limit_remaining,
    }


def _windows_from_json(items: Iterable[dict]) -> dict[str, QuotaWindow]:
    result: dict[str, QuotaWindow] = {}
    for item in items:
        try:
            w = QuotaWindow.model_validate(item)
            result[w.name] = w
        except Exception:
            continue
    return result


def _hour_bucket(dt: datetime) -> str:
    return _aware(dt).strftime("%Y%m%d%H")


def _event_title(provider: str, event_type: EventType) -> str:
    name = PROVIDERS.get(provider).name if provider in PROVIDERS else provider
    return {
        EventType.QUOTA_RESET: f"{name}: quota reset",
        EventType.QUOTA_INCREASE: f"{name}: limits increased",
        EventType.QUOTA_DECREASE: f"{name}: limits reduced",
        EventType.POLICY_CHANGE: f"{name}: usage policy changed",
        EventType.PROMO_CREDIT: f"{name}: bonus quota/reset available",
        EventType.OUTAGE_COMPENSATION: f"{name}: quota compensation",
        EventType.PERSONAL_RESET: f"{name}: your quota reset",
    }[event_type]


class EventEngine:
    def __init__(self, state: StateStore = store):
        self.state = state

    def ingest_sensor(self, report: SensorReport) -> list[EventRecord]:
        report.collected_at = _aware(report.collected_at)
        created: list[EventRecord] = []
        previous = self.state.get_snapshot(report.sensor_id, report.provider)

        if previous:
            prev_windows = _windows_from_json(previous.get("windows", []))
            now_windows = {w.name: w for w in report.windows}
            for name, current in now_windows.items():
                old = prev_windows.get(name)
                if not old:
                    continue
                drop = old.used_percent - current.used_percent
                if old.used_percent < 55 or current.used_percent > 15 or drop < settings.global_reset_drop_percent:
                    continue

                expected = False
                if old.reset_at:
                    delta = abs((report.collected_at - _aware(old.reset_at)).total_seconds())
                    expected = delta <= settings.expected_reset_tolerance_minutes * 60

                if expected:
                    fp = f"personal:{report.sensor_id}:{report.provider}:{name}:{_hour_bucket(report.collected_at)}"
                    created.append(self.state.upsert_event(
                        fingerprint=fp, provider=report.provider, event_type=EventType.PERSONAL_RESET.value,
                        confidence=Confidence.CONFIRMED.value, title=_event_title(report.provider, EventType.PERSONAL_RESET),
                        summary=f"{name} reset observed: {old.used_percent:.0f}% → {current.used_percent:.0f}% used.",
                        occurred_at=report.collected_at, meta={"window": name, "scheduled": True},
                    ))
                    continue

                fp = f"crowd:{report.provider}:quota_reset:{_hour_bucket(report.collected_at)}"
                evidence_count = self.state.add_evidence(
                    fp, report.sensor_id, report.collected_at,
                    {"window": name, "from": old.used_percent, "to": current.used_percent},
                )
                confidence = Confidence.CONFIRMED if evidence_count >= settings.global_confirm_sensor_count else Confidence.DETECTED
                created.append(self.state.upsert_event(
                    fingerprint=fp, provider=report.provider, event_type=EventType.QUOTA_RESET.value,
                    confidence=confidence.value, title=_event_title(report.provider, EventType.QUOTA_RESET),
                    summary=(f"Unexpected quota reset detected across {evidence_count} independent sensor(s). "
                             f"Latest {name}: {old.used_percent:.0f}% → {current.used_percent:.0f}% used."),
                    occurred_at=report.collected_at, evidence_count=evidence_count,
                    meta={"crowd_confirmed": confidence == Confidence.CONFIRMED},
                ))

        self.state.put_snapshot(
            report.sensor_id, report.provider, report.collected_at,
            [_window_dict(w) for w in report.windows], report.meta,
        )
        return created

    async def ingest_announcement(self, announcement: Announcement) -> EventRecord | None:
        source_key = hashlib.sha256(f"{announcement.source}|{announcement.source_ref}".encode()).hexdigest()
        if self.state.source_seen(source_key):
            return None
        self.state.mark_source_seen(source_key)

        c = await classify(announcement.text)
        if not c.relevant or not c.event_type or c.confidence < 0.65:
            return None

        occurred = _aware(announcement.published_at)
        fp = f"official:{announcement.provider}:{c.event_type.value}:{_hour_bucket(occurred)}"
        return self.state.upsert_event(
            fingerprint=fp, provider=announcement.provider, event_type=c.event_type.value,
            confidence=Confidence.OFFICIAL.value if announcement.official else Confidence.CONFIRMED.value,
            title=_event_title(announcement.provider, c.event_type), summary=c.summary,
            occurred_at=occurred, source_url=announcement.url,
            meta={"source": announcement.source, "source_ref": announcement.source_ref, "classifier_confidence": c.confidence},
        )
