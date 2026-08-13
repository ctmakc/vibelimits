from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from .config import settings
from .db import EventRow, SessionLocal
from .engine import EventEngine
from .providers import PROVIDERS
from .schemas import Announcement, EventOut, SensorReport


engine = EventEngine(SessionLocal)
app = FastAPI(title="VibeLimits", version="0.1.0")


def sensor_auth(x_sensor_secret: str | None = Header(default=None)) -> None:
    if settings.sensor_shared_secret and x_sensor_secret != settings.sensor_shared_secret:
        raise HTTPException(401, "bad sensor secret")


def admin_auth(authorization: str | None = Header(default=None)) -> None:
    if settings.admin_token and authorization != f"Bearer {settings.admin_token}":
        raise HTTPException(401, "bad admin token")


def serialize_event(e: EventRow) -> EventOut:
    return EventOut(
        id=e.id, provider=e.provider, event_type=e.event_type, confidence=e.confidence,
        title=e.title, summary=e.summary, occurred_at=e.occurred_at,
        evidence_count=e.evidence_count, source_url=e.source_url, meta=e.meta or {},
    )


@app.get("/health")
def health():
    return {"ok": True, "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/providers")
def providers():
    return [{"id": p.id, "name": p.name, "reset_model": p.reset_model, "docs_url": p.docs_url, "local_sensor": p.local_sensor} for p in PROVIDERS.values()]


@app.get("/api/v1/events", response_model=list[EventOut])
def events(provider: str | None = None, limit: int = Query(default=50, ge=1, le=500), include_detected: bool = False):
    with SessionLocal() as db:
        q = select(EventRow).order_by(EventRow.occurred_at.desc()).limit(limit)
        if provider:
            q = q.where(EventRow.provider == provider)
        if not include_detected:
            q = q.where(EventRow.confidence.in_(["confirmed", "official"]))
        return [serialize_event(e) for e in db.execute(q).scalars().all()]


@app.post("/api/v1/sensor/report", dependencies=[Depends(sensor_auth)])
def sensor_report(report: SensorReport):
    events = engine.ingest_sensor(report)
    return {"accepted": True, "events": [serialize_event(e).model_dump(mode="json") for e in events]}


@app.post("/api/v1/admin/announcement", dependencies=[Depends(admin_auth)])
async def admin_announcement(announcement: Announcement):
    event = await engine.ingest_announcement(announcement)
    return {"accepted": True, "event": serialize_event(event).model_dump(mode="json") if event else None}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    cards = "".join(f'<div class="provider"><b>{p.name}</b><span>{p.reset_model}</span></div>' for p in PROVIDERS.values())
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VibeLimits</title><style>
body{{font-family:Inter,system-ui,sans-serif;background:#0b0d10;color:#f4f5f7;margin:0;max-width:1100px;padding:48px 24px;margin:auto}}
h1{{font-size:52px;margin:0}} .sub{{color:#9aa4b2;font-size:20px;margin:12px 0 36px}} #events{{display:grid;gap:12px;margin-top:28px}}
.event,.provider{{border:1px solid #262b33;background:#12151a;border-radius:14px;padding:18px}} .provider span{{display:block;color:#8c96a5;margin-top:6px}}
.providers{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}} .badge{{font-size:12px;border:1px solid #3b424d;border-radius:20px;padding:3px 8px;margin-left:8px;color:#b8c0cc}}
a{{color:#8ab4ff}} h2{{margin-top:42px}}
</style></head><body><h1>VibeLimits</h1><div class="sub">The quota radar for AI coding agents.</div>
<div class="providers">{cards}</div><h2>Latest confirmed events</h2><div id="events">Loading…</div>
<script>fetch('/api/v1/events?limit=30').then(r=>r.json()).then(xs=>{{document.getElementById('events').innerHTML=xs.length?xs.map(x=>`<div class="event"><b>${{x.title}}</b><span class="badge">${{x.confidence}}</span><p>${{x.summary}}</p><small>${{new Date(x.occurred_at).toLocaleString()}} · evidence ${{x.evidence_count}}</small></div>`).join(''):'No events yet.'}})</script></body></html>'''
