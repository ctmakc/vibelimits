from __future__ import annotations

from datetime import datetime, timezone


def _timestamp(value):
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except Exception:
        return None


def _num(obj: dict, *keys, default=None):
    for key in keys:
        if key in obj and obj[key] is not None:
            try:
                return float(obj[key])
            except (TypeError, ValueError):
                pass
    return default


def parse_rate_limits(result: dict) -> list[dict]:
    root = result.get("rateLimitsByLimitId") or result.get("rate_limits_by_limit_id") or {}
    if not root:
        snap = result.get("rateLimits") or result.get("rate_limits") or result
        root = {"codex": snap}
    windows: list[dict] = []
    for limit_id, snap in root.items():
        if not isinstance(snap, dict):
            continue
        for label in ("primary", "secondary"):
            w = snap.get(label)
            if not isinstance(w, dict):
                continue
            used = _num(w, "usedPercent", "used_percent")
            if used is None:
                continue
            reset_raw = w.get("resetsAt", w.get("resetAt", w.get("resets_at", w.get("reset_at"))))
            window_minutes = _num(w, "windowMinutes", "window_minutes", "windowDurationMins", "window_duration_mins")
            windows.append({
                "name": f"{limit_id}:{label}",
                "used_percent": max(0, min(100, used)),
                "reset_at": _timestamp(reset_raw),
                "window_minutes": int(window_minutes) if window_minutes is not None else None,
            })
    return windows
