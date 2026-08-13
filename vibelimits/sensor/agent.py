from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from .codex import parse_rate_limits
from .openusage import normalize_openusage


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
        {"sensor_id": sid, "provider": p, "windows": windows, "meta": {"agent_version": "0.1.0", **meta}}
        for p, windows, meta in batches if windows
    ]


def cli() -> None:
    parser = argparse.ArgumentParser(description="VibeLimits privacy-preserving quota normalizer")
    parser.add_argument("--input", help="JSON file; omit to read stdin")
    parser.add_argument("--format", choices=["auto", "codex", "openusage", "normalized"], default="auto")
    parser.add_argument("--provider", help="Provider id for normalized input")
    args = parser.parse_args()
    print(json.dumps(normalize(read_payload(args.input), args.format, args.provider), indent=2))


if __name__ == "__main__":
    cli()
