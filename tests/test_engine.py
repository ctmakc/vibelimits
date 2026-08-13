from datetime import datetime, timedelta, timezone

from vibelimits.engine import EventEngine
from vibelimits.schemas import Confidence, QuotaWindow, SensorReport
from vibelimits.state import StateStore


def make_report(sensor, used, when, reset_at=None):
    return SensorReport(sensor_id=sensor, provider="codex", collected_at=when, windows=[QuotaWindow(name="weekly", used_percent=used, reset_at=reset_at)])


def test_global_reset_requires_three_reports(tmp_path):
    state = StateStore(str(tmp_path / "state.json"))
    engine = EventEngine(state)
    now = datetime.now(timezone.utc)
    sensors = ("sensor-0001", "sensor-0002", "sensor-0003")
    for sensor in sensors:
        engine.ingest_sensor(make_report(sensor, 90, now))
    states = []
    for sensor in sensors:
        events = engine.ingest_sensor(make_report(sensor, 0, now + timedelta(minutes=5)))
        states.append(events[-1].confidence)
    assert states == [Confidence.DETECTED.value, Confidence.DETECTED.value, Confidence.CONFIRMED.value]


def test_scheduled_reset_is_personal(tmp_path):
    state = StateStore(str(tmp_path / "state.json"))
    engine = EventEngine(state)
    now = datetime.now(timezone.utc)
    engine.ingest_sensor(make_report("sensor-0001", 90, now, reset_at=now + timedelta(minutes=5)))
    events = engine.ingest_sensor(make_report("sensor-0001", 0, now + timedelta(minutes=5)))
    assert events[-1].event_type == "personal_reset"
