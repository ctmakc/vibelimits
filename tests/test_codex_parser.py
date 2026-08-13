from vibelimits.sensor.codex import parse_rate_limits


def test_codex_camel_case():
    payload = {"rateLimitsByLimitId": {"codex": {"primary": {"usedPercent": 84.5, "windowMinutes": 300, "resetsAt": 1893456000}, "secondary": {"usedPercent": 40, "windowMinutes": 10080, "resetsAt": 1893542400}}}}
    windows = parse_rate_limits(payload)
    assert len(windows) == 2
    assert windows[0]["name"] == "codex:primary"
    assert windows[0]["used_percent"] == 84.5


def test_codex_legacy_single_bucket():
    payload = {"rateLimits": {"primary": {"used_percent": 12, "window_minutes": 300, "reset_at": 1893456000}}}
    windows = parse_rate_limits(payload)
    assert windows[0]["used_percent"] == 12
