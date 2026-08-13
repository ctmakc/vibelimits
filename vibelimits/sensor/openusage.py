from __future__ import annotations


def normalize_openusage(payload: dict) -> list[tuple[str, list[dict], dict]]:
    """Best-effort normalization across OpenUsage versions.

    Missing quota fields produce no report rather than guessed data.
    """
    candidates = payload.get("snapshots") if isinstance(payload, dict) else None
    if not isinstance(candidates, list):
        candidates = payload if isinstance(payload, list) else []
    result: list[tuple[str, list[dict], dict]] = []
    provider_alias = {
        "claude_code": "claude_code", "codex": "codex", "cursor": "cursor",
        "gemini_cli": "gemini_cli", "copilot": "copilot", "windsurf": "windsurf",
        "kiro": "kiro", "zed": "zed", "opencode": "opencode", "amp": "amp",
        "roo_code": "roo_code",
    }
    for snap in candidates:
        if not isinstance(snap, dict):
            continue
        raw_provider = str(snap.get("provider") or snap.get("system") or snap.get("id") or "").lower().replace("-", "_")
        provider = provider_alias.get(raw_provider)
        if not provider:
            continue
        windows: list[dict] = []
        raw_windows = snap.get("quota_windows") or snap.get("quotaWindows") or snap.get("limits") or snap.get("windows") or []
        if isinstance(raw_windows, dict):
            raw_windows = [{"name": k, **v} for k, v in raw_windows.items() if isinstance(v, dict)]
        for idx, window in enumerate(raw_windows if isinstance(raw_windows, list) else []):
            if not isinstance(window, dict):
                continue
            used = window.get("used_percent", window.get("usedPercent", window.get("percent_used")))
            if used is None and window.get("remaining_percent") is not None:
                used = 100 - float(window["remaining_percent"])
            try:
                used = float(used)
            except (TypeError, ValueError):
                continue
            windows.append({
                "name": str(window.get("name") or window.get("label") or f"window-{idx}"),
                "used_percent": max(0, min(100, used)),
                "reset_at": window.get("reset_at") or window.get("resetAt") or window.get("resets_at"),
                "window_minutes": window.get("window_minutes") or window.get("windowMinutes"),
                "limit_total": window.get("limit_total") or window.get("limit"),
                "limit_remaining": window.get("limit_remaining") or window.get("remaining"),
            })
        if windows:
            result.append((provider, windows, {"source": "openusage"}))
    return result
