from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass
class EventRecord:
    id: str
    fingerprint: str
    provider: str
    event_type: str
    confidence: str
    title: str
    summary: str
    occurred_at: datetime
    evidence_count: int = 1
    source_url: str | None = None
    meta: dict | None = None
    dispatched_at: datetime | None = None

    def to_json(self) -> dict:
        d = asdict(self)
        d["occurred_at"] = aware(self.occurred_at).isoformat()
        d["dispatched_at"] = aware(self.dispatched_at).isoformat() if self.dispatched_at else None
        d["meta"] = self.meta or {}
        return d

    @classmethod
    def from_json(cls, data: dict) -> "EventRecord":
        data = dict(data)
        data["occurred_at"] = datetime.fromisoformat(data["occurred_at"])
        if data.get("dispatched_at"):
            data["dispatched_at"] = datetime.fromisoformat(data["dispatched_at"])
        return cls(**data)


class StateStore:
    def __init__(self, path: str | None = None):
        self.path = Path(path or os.getenv("STATE_FILE", "./vibelimits-state.json"))
        self.lock = threading.RLock()
        self.data = {
            "snapshots": {},
            "evidence": {},
            "events": {},
            "seen_sources": [],
            "subscriptions": {},
        }
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text())
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except Exception:
            return

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True))
        tmp.replace(self.path)

    def snapshot_key(self, sensor_id: str, provider: str) -> str:
        return f"{sensor_id}:{provider}"

    def get_snapshot(self, sensor_id: str, provider: str) -> dict | None:
        with self.lock:
            return self.data["snapshots"].get(self.snapshot_key(sensor_id, provider))

    def put_snapshot(self, sensor_id: str, provider: str, collected_at: datetime, windows: list[dict], meta: dict) -> None:
        with self.lock:
            self.data["snapshots"][self.snapshot_key(sensor_id, provider)] = {
                "collected_at": aware(collected_at).isoformat(),
                "windows": windows,
                "meta": meta,
            }
            self._save()

    def add_evidence(self, fingerprint: str, sensor_id: str, observed_at: datetime, meta: dict) -> int:
        with self.lock:
            evidence = self.data["evidence"].setdefault(fingerprint, {})
            evidence.setdefault(sensor_id, {"observed_at": aware(observed_at).isoformat(), "meta": meta})
            self._save()
            return len(evidence)

    def source_seen(self, key: str) -> bool:
        with self.lock:
            return key in set(self.data["seen_sources"])

    def mark_source_seen(self, key: str) -> None:
        with self.lock:
            if key not in self.data["seen_sources"]:
                self.data["seen_sources"].append(key)
                self._save()

    def upsert_event(self, *, fingerprint: str, provider: str, event_type: str, confidence: str,
                     title: str, summary: str, occurred_at: datetime, evidence_count: int = 1,
                     source_url: str | None = None, meta: dict | None = None) -> EventRecord:
        with self.lock:
            existing = self.data["events"].get(fingerprint)
            if existing:
                event = EventRecord.from_json(existing)
                rank = {"detected": 1, "confirmed": 2, "official": 3}
                if rank.get(confidence, 0) > rank.get(event.confidence, 0):
                    event.confidence = confidence
                event.evidence_count = max(event.evidence_count, evidence_count)
                event.summary = summary
                if source_url:
                    event.source_url = source_url
                event.meta = {**(event.meta or {}), **(meta or {})}
            else:
                event = EventRecord(
                    id=str(uuid.uuid4()), fingerprint=fingerprint, provider=provider,
                    event_type=event_type, confidence=confidence, title=title, summary=summary,
                    occurred_at=aware(occurred_at), evidence_count=evidence_count,
                    source_url=source_url, meta=meta or {},
                )
            self.data["events"][fingerprint] = event.to_json()
            self._save()
            return event

    def list_events(self, provider: str | None = None, limit: int = 50, include_detected: bool = False) -> list[EventRecord]:
        with self.lock:
            events = [EventRecord.from_json(x) for x in self.data["events"].values()]
        if provider:
            events = [e for e in events if e.provider == provider]
        if not include_detected:
            events = [e for e in events if e.confidence in {"confirmed", "official"}]
        events.sort(key=lambda e: e.occurred_at, reverse=True)
        return events[:limit]

    def pending_events(self, limit: int = 50) -> list[EventRecord]:
        events = [e for e in self.list_events(limit=10000, include_detected=False) if not e.dispatched_at]
        events.sort(key=lambda e: e.occurred_at)
        return events[:limit]

    def mark_dispatched(self, fingerprint: str) -> None:
        with self.lock:
            raw = self.data["events"].get(fingerprint)
            if not raw:
                return
            event = EventRecord.from_json(raw)
            event.dispatched_at = utcnow()
            self.data["events"][fingerprint] = event.to_json()
            self._save()

    def get_subscription(self, recipient_id: str) -> dict | None:
        with self.lock:
            return self.data["subscriptions"].get(recipient_id)

    def set_subscription(self, recipient_id: str, enabled: bool, provider_filters: list[str] | None = None) -> None:
        with self.lock:
            current = self.data["subscriptions"].get(recipient_id, {})
            current["enabled"] = enabled
            if provider_filters is not None:
                current["provider_filters"] = provider_filters
            current.setdefault("provider_filters", [])
            self.data["subscriptions"][recipient_id] = current
            self._save()

    def active_subscriptions(self) -> dict[str, dict]:
        with self.lock:
            return {k: dict(v) for k, v in self.data["subscriptions"].items() if v.get("enabled")}


store = StateStore()
