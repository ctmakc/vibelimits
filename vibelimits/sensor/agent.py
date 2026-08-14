from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import httpx

from .codex import parse_rate_limits
from .openusage import normalize_openusage

DEFAULT_API = "https://heocjdyufceudxdbghck.supabase.co/functions/v1/vibelimits-api"


def state_dir() -> Path:
    path = Path.home() / ".config" / "vibelimits"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sensor_id() -> str:
    path = state_dir() / "sensor-id"
    if path.exists():
        value = path.read_text().strip()
        if value:
            return value
    value = str(uuid.uuid4())
    path.write_text(value)
    return value


def token_path() -> Path:
    return state_dir() / "sensor-token"


def read_payload(path: str | None) -> object:
    if path:
        return json.loads(Path(path).read_text())
    if sys.stdin.isatty():
        raise SystemExit("Pass --input FILE or pipe JSON to stdin")
    return json.load(sys.stdin)


def normalize(payload: object, fmt: str, provider: str | None) -> list[dict]:
    batches: list[tuple[str, list[dict], dict]]
    if fmt == "codex":
        if not isinstance(payload, dict):
            raise SystemExit("Codex input must be a JSON object")
        windows = parse_rate_limits(payload)
        batches = [(provider or "codex", windows, {"source": "stdin:codex"})] if windows else []
    elif fmt == "openusage":
        batches = normalize_openusage(payload)  # type: ignore[arg-type]
    elif fmt == "normalized":
        if not provider:
            raise SystemExit("--provider is required for --format normalized")
        if not isinstance(payload, dict) or not isinstance(payload.get("windows"), list):
            raise SystemExit("Normalized input requires a windows array")
        batches = [(provider, payload["windows"], {"source": "stdin:normalized"})]
    elif isinstance(payload, dict) and ("rateLimits" in payload or "rateLimitsByLimitId" in payload or "rate_limits" in payload):
        return normalize(payload, "codex", provider)
    else:
        return normalize(payload, "openusage", provider)

    sid = sensor_id()
    return [
        {"sensor_id": sid, "provider": p, "windows": windows, "meta": {"agent_version": "0.2.0", **meta}}
        for p, windows, meta in batches if windows
    ]


def ensure_token(api: str, sid: str) -> str:
    path = token_path()
    if path.exists() and path.read_text().strip():
        return path.read_text().strip()
    with httpx.Client(timeout=20) as client:
        r = client.post(f"{api.rstrip('/')}/sensor/register", json={"sensor_id": sid})
        r.raise_for_status()
        token = r.json()["token"]
    path.write_text(token)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return token


def submit(reports: list[dict], api: str) -> list[dict]:
    if not reports:
        return []
    token = ensure_token(api, reports[0]["sensor_id"])
    results: list[dict] = []
    with httpx.Client(timeout=20) as client:
        for report in reports:
            r = client.post(
                f"{api.rstrip('/')}/sensor/report",
                json=report,
                headers={"x-sensor-token": token},
            )
            r.raise_for_status()
            results.append(r.json())
    return results


def cli() -> None:
    parser = argparse.ArgumentParser(description="VibeLimits privacy-preserving quota normalizer")
    parser.add_argument("--input", help="JSON file; omit to read stdin")
    parser.add_argument("--format", choices=["auto", "codex", "openusage", "normalized"], default="auto")
    parser.add_argument("--provider", help="Provider id for normalized input")
    parser.add_argument("--submit", action="store_true", help="Register this installation if needed and submit normalized reports")
    parser.add_argument("--api", default=DEFAULT_API, help="VibeLimits API base URL")
    args = parser.parse_args()
    reports = normalize(read_payload(args.input), args.format, args.provider)
    if args.submit:
        print(json.dumps({"reports": reports, "server": submit(reports, args.api)}, indent=2))
    else:
        print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    cli()
