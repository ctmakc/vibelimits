# VibeLimits

> **The quota radar for AI coding agents.**

[![CI](https://github.com/ctmakc/vibelimits/actions/workflows/ci.yml/badge.svg)](https://github.com/ctmakc/vibelimits/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)

VibeLimits watches official provider announcements and privacy-preserving local quota sensors, correlates real resets, and sends useful alerts before you waste time refreshing five different usage dashboards.

**One feed for Codex, Claude Code, Cursor, Windsurf, Gemini CLI, GitHub Copilot and the rest of the AI-coding stack.**

## Why this exists

AI coding limits change constantly: rolling windows reset, weekly caps refill, providers grant bonus resets, outages trigger compensation, and temporary quota increases appear with little warning.

The information is fragmented across product UIs, X posts, changelogs, GitHub releases and individual accounts. VibeLimits normalizes those signals into one event stream.

Typical alert:

```text
🔥 OpenAI Codex: quota reset
Unexpected quota reset confirmed across independent sensors.

CONFIRMED · evidence: 7
```

## What works today

- **13-provider registry:** Codex, Claude Code, Cursor, Windsurf, Gemini CLI, GitHub Copilot, Kiro, Zed, OpenCode, Amp, Cline, Roo Code and GitHub Spark.
- **Official-source monitoring:** X API v2 plus RSS/Atom/GitHub release feeds.
- **Crowd confirmation:** unexpected drops are promoted from `detected` to `confirmed` only after independent sensors agree.
- **False-positive protection:** a user's normal scheduled reset is kept separate from a provider-wide reset.
- **Native Codex sensor:** uses `codex app-server` and `account/rateLimits/read` rather than screen scraping.
- **Broad local adapter:** optionally consumes local JSON from [OpenUsage](https://github.com/janekbaraniewski/openusage) for additional coding agents.
- **Telegram:** channel broadcasting plus personal subscriptions and provider filters.
- **Public API + dashboard:** normalized event feed for humans and integrations.
- **Self-hosted:** Docker Compose, SQLite by default, PostgreSQL-ready through SQLAlchemy.

## Provider coverage

| Provider | Official alerts | Crowd detection | Local quota sensor |
|---|:---:|:---:|:---:|
| OpenAI Codex | ✅ | ✅ | **Native** |
| Claude Code | ✅ | ✅ | OpenUsage adapter* |
| Cursor | ✅ | ✅ | OpenUsage adapter* |
| Windsurf | ✅ | ✅ | OpenUsage adapter* |
| Gemini CLI | ✅ | ✅ | OpenUsage adapter* |
| GitHub Copilot | ✅ | ✅ | OpenUsage adapter* |
| Kiro | configurable | ✅ | OpenUsage adapter* |
| Zed AI | configurable | ✅ | OpenUsage adapter* |
| OpenCode | configurable | ✅ | OpenUsage adapter* |
| Amp | configurable | ✅ | OpenUsage adapter* |
| Roo Code | configurable | ✅ | OpenUsage adapter* |
| Cline | configurable | ✅ | crowd/manual |
| GitHub Spark | configurable | ✅ | crowd/manual |

\* Best-effort: a provider is reported only when the local OpenUsage snapshot exposes quota-window fields. Missing fields degrade to no report, not a fabricated signal.

See [`docs/PROVIDERS.md`](docs/PROVIDERS.md) for details.

## Quick start

### Server

```bash
git clone https://github.com/ctmakc/vibelimits.git
cd vibelimits
cp .env.example .env
# Set ADMIN_TOKEN and SENSOR_SHARED_SECRET at minimum.
docker compose up -d --build
```

Open `http://localhost:8080`.

Useful endpoints:

```text
GET  /health
GET  /api/v1/providers
GET  /api/v1/events
POST /api/v1/sensor/report
POST /api/v1/admin/announcement
```

### Telegram

Set these values in `.env`:

```dotenv
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHANNEL_ID=...
```

Bot commands:

```text
/start
/stop
/status
/providers
/only codex,claude_code,cursor
/all
/latest
```

### Local sensor

Run the sensor on a developer machine where the coding tools are already configured:

```bash
pip install -e .
VIBELIMITS_SERVER=https://limits.example.com \
VIBELIMITS_SENSOR_SECRET='...' \
vibelimits-sensor --interval 120
```

Codex is read natively through its local app-server. For broader coverage, install OpenUsage on the same machine; VibeLimits consumes its local machine-readable output when available.

## Event model

| Confidence | Meaning |
|---|---|
| `detected` | early crowd candidate; not broadcast globally |
| `confirmed` | independent evidence crossed the configured threshold |
| `official` | classified official provider announcement |

Event types currently include:

`quota_reset`, `quota_increase`, `quota_decrease`, `policy_change`, `promo_credit`, `outage_compensation`, `personal_reset`.

## Privacy model

The local sensor is intentionally narrow. It sends normalized quota-window data and pseudonymous installation/account identifiers.

It does **not** send OAuth tokens, API keys, prompts, source code, repository contents, file names, command output or conversation history.

Crowd signals should answer one question only: **did a quota window materially change, and when?**

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`SECURITY.md`](SECURITY.md).

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Current baseline: **7 tests** covering classification, Codex parsing and reset correlation.

## Adding another provider

The provider registry is data-driven. Most new integrations need only:

1. a provider entry in `vibelimits/providers.py`;
2. official source configuration;
3. optional local snapshot normalization.

The event engine, API and Telegram delivery remain unchanged.

Provider requests are welcome through GitHub Issues.

## Roadmap

Near-term priorities:

- Discord and webhook delivery;
- signed sensor registration instead of one shared sensor secret;
- richer provider-specific adapters;
- historical reset timelines and reset-frequency analytics;
- public embeddable status badges;
- confidence scoring by source quality and sensor diversity;
- optional reset-probability forecasting.

See [`ROADMAP.md`](ROADMAP.md).

## Deployment

For a public instance:

1. terminate TLS in a reverse proxy or managed platform;
2. use strong `ADMIN_TOKEN` and `SENSOR_SHARED_SECRET` values;
3. switch to PostgreSQL as traffic grows;
4. run source polling as a singleton worker if horizontally scaling the API;
5. keep X/LLM/Telegram credentials outside the repository.

Full notes: [`docs/SELF_HOSTING.md`](docs/SELF_HOSTING.md).

## Contributing

PRs and provider adapters are welcome. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

VibeLimits is an independent open-source project and is not affiliated with or endorsed by the providers it monitors.
