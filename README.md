# VibeLimits

> **The quota radar for AI coding agents.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

VibeLimits monitors AI-coding quota changes, correlates unexpected resets across independent installations, and publishes useful alerts in one place.

Supported registry: **Codex, Claude Code, Cursor, Windsurf, Gemini CLI, GitHub Copilot, Kiro, Zed, OpenCode, Amp, Cline, Roo Code and GitHub Spark.**

## What works today

- X API v2 and RSS/Atom official-source collectors;
- crowd reset correlation with configurable confirmation threshold;
- scheduled personal-reset suppression;
- Codex rate-limit payload parser;
- OpenUsage JSON normalizer for additional coding tools;
- Telegram channel delivery and personal provider filters;
- FastAPI event API and minimal web dashboard;
- lightweight JSON state store;
- 7 tests covering classification, Codex parsing and reset correlation.

A reset starts as `detected` and becomes `confirmed` only after enough independent installations report the same unexpected quota drop. Official provider announcements are stored as `official`.

## Quick start

```bash
git clone https://github.com/ctmakc/vibelimits.git
cd vibelimits
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Run the API/dashboard:

```bash
vibelimits
```

Run official-source monitoring and Telegram delivery in a second process:

```bash
vibelimits-worker --interval 60
```

Open `http://localhost:8080`.

Endpoints:

```text
GET  /health
GET  /api/v1/providers
GET  /api/v1/events
POST /api/v1/sensor/report
```

## Telegram

Set `TELEGRAM_BOT_TOKEN` and optionally `TELEGRAM_CHANNEL_ID` in `.env`.

Commands: `/start`, `/stop`, `/status`, `/providers`, `/only codex,claude_code,cursor`, `/all`, `/latest`.

## Local quota reports

`vibelimits-sensor` normalizes local JSON into VibeLimits sensor reports. It emits quota-window data plus a random installation UUID.

```bash
openusage export --json | vibelimits-sensor --format openusage
cat codex-rate-limits.json | vibelimits-sensor --format codex
```

A report sent to `POST /api/v1/sensor/report` contains:

```json
{
  "sensor_id": "random-installation-uuid",
  "provider": "codex",
  "windows": [
    {"name": "weekly", "used_percent": 87, "reset_at": "2026-08-17T12:00:00Z"}
  ]
}
```

The sensor design intentionally excludes prompts, source code, repository contents and account identity data.

## Development

```bash
pip install -e '.[dev]'
pytest -q
```

## Roadmap

Next: Discord/webhooks, signed sensor registration, richer provider adapters, historical reset timelines, confidence scoring and reset-probability forecasting.

See [`ROADMAP.md`](ROADMAP.md).

## License

Apache-2.0. VibeLimits is independent and is not affiliated with the providers it monitors.
