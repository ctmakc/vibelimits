from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError

from .classifier import classify
from .config import settings
from .db import EventRow, EvidenceRow, SeenSourceRow, SnapshotRow
from .providers import PROVIDERS
from .schemas import Announcement, Confidence, EventType, QuotaWindow, SensorReport


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
    dt = _aware(dt)
    return dt.strftime("%Y%m%d%H")


def _event_title(provider: str, event_type: EventType) -> str:
    name = PROVIDERS.get(provider).name if provider in PROVIDERS else provider
    titles = {
        EventType.QUOTA_RESET: f"{name}: quota reset",
        EventType.QUOTA_INCREASE: f"{name}: limits increased",
        EventType.QUOTA_DECREASE: f"{name}: limits reduced",
        EventType.POLICY_CHANGE: f"{name}: usage policy changed",
        EventType.PROMO_CREDIT: f"{name}: bonus quota/reset available",
        EventType.OUTAGE_COMPENSATION: f"{name}: quota compensation",
        EventType.PERSONAL_RESET: f"{name}: your quota reset",
    }
    return titles[event_type]


class EventEngine:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def ingest_sensor(self, report: SensorReport) -> list[EventRow]:
        report.collected_at = _aware(report.collected_at)
        created: list[EventRow] = []
        with self.session_factory() as db:
            previous = db.execute(
                select(SnapshotRow)
                .where(
                    SnapshotRow.sensor_id == report.sensor_id,
                    SnapshotRow.provider == report.provider,
                )
                .order_by(desc(SnapshotRow.collected_at))
                .limit(1)
            ).scalar_one_or_none()

            row = SnapshotRow(
                sensor_id=report.sensor_id,
                provider=report.provider,
                collected_at=report.collected_at,
                windows=[_window_dict(w) for w in report.windows],
                meta=report.meta,
            )
            db.add(row)

            if previous:
                prev_windows = _windows_from_json(previous.windows)
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
                        delta = abs((_aware(report.collected_at) - _aware(old.reset_at)).total_seconds())
                        expected = delta <= settings.expected_reset_tolerance_minutes * 60

                    if expected:
                        fp = f"personal:{report.sensor_id}:{report.provider}:{name}:{_hour_bucket(report.collected_at)}"
                        event = self._upsert_event(
                            db,
                            fingerprint=fp,
                            provider=report.provider,
                            event_type=EventType.PERSONAL_RESET,
                            confidence=Confidence.CONFIRMED,
                            title=_event_title(report.provider, EventType.PERSONAL_RESET),
                            summary=f"{name} reset observed: {old.used_percent:.0f}% → {current.used_percent:.0f}% used.",
                            occurred_at=report.collected_at,
                            meta={"window": name, "scheduled": True},
                        )
                        created.append(event)
                        continue

                    fp = f"crowd:{report.provider}:quota_reset:{_hour_bucket(report.collected_at)}"
                    try:
                        db.add(EvidenceRow(
                            fingerprint=fp,
                            sensor_id=report.sensor_id,
                            observed_at=report.collected_at,
                            meta={"window": name, "from": old.used_percent, "to": current.used_percent},
                        ))
                        db.flush()
                    except IntegrityError:
                        db.rollback()
                        db.add(row)
                        continue

                    evidence_count = db.execute(
                        select(func.count(EvidenceRow.id)).where(EvidenceRow.fingerprint == fp)
                    ).scalar_one()
                    confidence = Confidence.CONFIRMED if evidence_count >= settings.global_confirm_sensor_count else Confidence.DETECTED
                    event = self._upsert_event(
                        db,
                        fingerprint=fp,
                        provider=report.provider,
                        event_type=EventType.QUOTA_RESET,
                        confidence=confidence,
                        title=_event_title(report.provider, EventType.QUOTA_RESET),
                        summary=(
                            f"Unexpected quota reset detected across {evidence_count} independent sensor(s). "
                            f"Latest {name}: {old.used_percent:.0f}% → {current.used_percent:.0f}% used."
                        ),
                        occurred_at=report.collected_at,
                        evidence_count=evidence_count,
                        meta={"crowd_confirmed": confidence == Confidence.CONFIRMED},
                    )
                    created.append(event)

            db.commit()
            return created

    async def ingest_announcement(self, announcement: Announcement) -> EventRow | None:
        source_key = hashlib.sha256(f"{announcement.source}|{announcement.source_ref}".encode()).hexdigest()
        with self.session_factory() as db:
            if db.get(SeenSourceRow, source_key):
                return None
            db.add(SeenSourceRow(key=source_key))
            db.commit()

        c = await classify(announcement.text)
        if not c.relevant or not c.event_type or c.confidence < 0.65:
            return None

        occurred = _aware(announcement.published_at)
        fp = f"official:{announcement.provider}:{c.event_type.value}:{_hour_bucket(occurred)}"
        with self.session_factory() as db:
            event = self._upsert_event(
                db,
                fingerprint=fp,
                provider=announcement.provider,
                event_type=c.event_type,
                confidence=Confidence.OFFICIAL if announcement.official else Confidence.CONFIRMED,
                title=_event_title(announcement.provider, c.event_type),
                summary=c.summary,
                occurred_at=occurred,
                source_url=announcement.url,
                meta={"source": announcement.source, "source_ref": announcement.source_ref, "classifier_confidence": c.confidence},
            )
            db.commit()
            return event

    def _upsert_event(
        self,
        db,
        *,
        fingerprint: str,
        provider: str,
        event_type: EventType,
        confidence: Confidence,
        title: str,
        summary: str,
        occurred_at: datetime,
        evidence_count: int = 1,
        source_url: str | None = None,
        meta: dict | None = None,
    ) -> EventRow:
        existing = db.execute(select(EventRow).where(EventRow.fingerprint == fingerprint)).scalar_one_or_none()
        if existing:
            rank = {Confidence.DETECTED.value: 1, Confidence.CONFIRMED.value: 2, Confidence.OFFICIAL.value: 3}
            if rank[confidence.value] > rank.get(existing.confidence, 0):
                existing.confidence = confidence.value
            existing.evidence_count = max(existing.evidence_count, evidence_count)
            existing.summary = summary
            if source_url:
                existing.source_url = source_url
            existing.meta = {**(existing.meta or {}), **(meta or {})}
            return existing

        event = EventRow(
            id=str(uuid.uuid4()),
            fingerprint=fingerprint,
            provider=provider,
            event_type=event_type.value,
            confidence=confidence.value,
            title=title,
            summary=summary,
            occurred_at=_aware(occurred_at),
            evidence_count=evidence_count,
            source_url=source_url,
            meta=meta or {},
        )
        db.add(event)
        db.flush()
        return event
