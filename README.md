# VibeLimits

> **The quota radar for AI coding agents.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)

VibeLimits monitors AI-coding quota changes, correlates unexpected resets across independent installations, and publishes useful alerts in one place.

Supported registry: **Codex, Claude Code, Cursor, Windsurf, Gemini CLI, GitHub Copilot, Kiro, Zed, OpenCode, Amp, Cline, Roo Code and GitHub Spark.**

## Live service

Production API + dashboard:

`https://heocjdyufceudxdbghck.supabase.co/functions/v1/vibelimits-api`

Endpoints:

```text
GET  /health
GET  /providers
GET  /events
POST /sensor/register
POST /sensor/report
```

The production backend runs on Supabase Edge Functions + Postgres. Historical entries are limited to source-backed official provider changes; global reset events require independent sensor evidence.

## What works today

- production Supabase Postgres event/state store;
- public Edge API and minimal live dashboard;
- crowd reset correlation with a 3-installation confirmation threshold;
- scheduled personal-reset suppression;
- privacy-preserving per-install sensor registration;
- Codex rate-limit payload parser;
- OpenUsage JSON normalizer for additional coding tools;
- X API v2 and RSS/Atom collectors in the self-hosted worker;
- Telegram channel delivery and personal provider filters in the self-hosted worker;
- 7 tests covering classification, Codex parsing and reset correlation.

A reset starts as `detected` and becomes `confirmed` only after three independent installations report the same unexpected quota drop. Official provider announcements are stored as `official`.

## Install the sensor

```bash
git clone https://github.com/ctmakc/vibelimits.git
cd vibelimits
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Normalize only:

```bash
openusage export --json | vibelimits-sensor --format openusage
cat codex-rate-limits.json | vibelimits-sensor --format codex
```

Normalize and submit to the live radar:

```bash
openusage export --json | vibelimits-sensor --format openusage --submit
cat codex-rate-limits.json | vibelimits-sensor --format codex --submit
```

On first submit VibeLimits creates a random installation token under `~/.config/vibelimits/`. Reports contain quota-window data and a random installation UUID. They intentionally exclude prompts, source code, repository contents, hostname and account identity.

## Self-hosted API / worker

```bash
cp .env.example .env
pip install -e '.[dev]'
vibelimits
```

Run official-source monitoring and Telegram delivery in a second process:

```bash
vibelimits-worker --interval 60
```

Local FastAPI endpoints remain available under `/api/v1/*` for self-hosted deployments.

## Telegram

Set `TELEGRAM_BOT_TOKEN` and optionally `TELEGRAM_CHANNEL_ID` in `.env`.

Commands: `/start`, `/stop`, `/status`, `/providers`, `/only codex,claude_code,cursor`, `/all`, `/latest`.

## Development

```bash
pip install -e '.[dev]'
pytest -q
```

## Roadmap

Next: Discord/webhooks, richer provider adapters, historical reset timelines, confidence scoring, reset-probability forecasting and a dedicated public frontend/domain.

See [`ROADMAP.md`](ROADMAP.md).

## License

Apache-2.0. VibeLimits is independent and is not affiliated with the providers it monitors.
