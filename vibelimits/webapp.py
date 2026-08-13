from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse

from .config import settings
from .engine import EventEngine
from .providers import PROVIDERS
from .schemas import EventOut, SensorReport
from .state import EventRecord, store


engine = EventEngine(store)
app = FastAPI(title="VibeLimits", version="0.1.0")


def sensor_auth(x_sensor_secret: str | None = Header(default=None)) -> None:
    if settings.sensor_shared_secret and x_sensor_secret != settings.sensor_shared_secret:
        raise HTTPException(401, "bad sensor secret")


def serialize_event(event: EventRecord) -> EventOut:
    return EventOut(
        id=event.id,
        provider=event.provider,
        event_type=event.event_type,
        confidence=event.confidence,
        title=event.title,
        summary=event.summary,
        occurred_at=event.occurred_at,
        evidence_count=event.evidence_count,
        source_url=event.source_url,
        meta=event.meta or {},
    )


@app.get("/health")
def health():
    return {"ok": True, "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/providers")
def providers():
    return [
        {
            "id": provider.id,
            "name": provider.name,
            "reset_model": provider.reset_model,
            "docs_url": provider.docs_url,
            "local_sensor": provider.local_sensor,
        }
        for provider in PROVIDERS.values()
    ]


@app.get("/api/v1/events", response_model=list[EventOut])
def events(
    provider: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    include_detected: bool = False,
):
    return [
        serialize_event(event)
        for event in store.list_events(provider=provider, limit=limit, include_detected=include_detected)
    ]


@app.post("/api/v1/sensor/report", dependencies=[Depends(sensor_auth)])
def sensor_report(report: SensorReport):
    events = engine.ingest_sensor(report)
    return {
        "accepted": True,
        "events": [serialize_event(event).model_dump(mode="json") for event in events],
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    cards = "".join(
        f'<div class="provider"><b>{provider.name}</b><span>{provider.reset_model}</span></div>'
        for provider in PROVIDERS.values()
    )
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
