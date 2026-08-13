# VibeLimits roadmap

VibeLimits is being built as a normalized quota-intelligence layer, not just a Telegram bot.

## v0.1 — working MVP

- [x] multi-provider registry
- [x] X + RSS/Atom official-source collectors
- [x] deterministic announcement classifier
- [x] optional OpenAI-compatible LLM classifier
- [x] privacy-preserving sensor reports
- [x] independent-sensor reset correlation
- [x] scheduled personal-reset suppression
- [x] native Codex app-server sensor
- [x] optional OpenUsage adapter
- [x] Telegram subscriptions and provider filters
- [x] public event API and minimal dashboard
- [x] Docker Compose and CI

## v0.2 — useful public service

- [ ] production PostgreSQL deployment
- [ ] Discord delivery
- [ ] generic signed webhooks
- [ ] per-provider event pages and history
- [ ] source/evidence inspector
- [ ] health page for collectors
- [ ] sensor registration keys instead of one shared secret
- [ ] rate limiting and abuse controls
- [ ] structured OpenAPI examples

## v0.3 — network effects

- [ ] one-command sensor installer for macOS/Linux
- [ ] anonymous sensor diversity scoring
- [ ] provider/plan/region segmentation where data supports it
- [ ] embeddable badges
- [ ] public historical dataset export
- [ ] bot localization

## Later

- [ ] reset probability / expected-next-event models
- [ ] team quota dashboards
- [ ] paid API/webhooks with higher history limits
- [ ] provider uptime/limit-change correlation
