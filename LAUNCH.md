# VibeLimits launch playbook

VibeLimits should be launched as a useful live utility, not as a generic "we built an app" announcement.

## Launch state

Public service:

`https://heocjdyufceudxdbghck.supabase.co/functions/v1/vibelimits-api`

Repository:

`https://github.com/ctmakc/vibelimits`

Current proof points:

- 13-provider registry;
- live Supabase/Postgres backend;
- official historical quota/policy events;
- privacy-preserving sensor registration;
- scheduled personal reset suppression;
- three independent installations required for a global crowd-confirmed reset;
- open-source sensor and backend reference implementation.

## Message hierarchy

1. **Pain:** coding-agent quotas are opaque and scattered across providers.
2. **Utility:** one live feed for resets, limit changes and policy moves.
3. **Trust:** a normal personal scheduled reset is not called global.
4. **Mechanism:** unexpected usage drops need three independent installations before confirmation.
5. **Privacy:** random install UUID + quota windows only; no prompts, code, repos, hostnames or account identity.
6. **Open source:** sensor code is inspectable.

## Best launch trigger

The strongest launch moment is the first genuine crowd-confirmed reset. Use the event itself as the headline:

> Codex just reset unexpectedly. VibeLimits confirmed it across 3 independent installations.

Until that happens, use official provider changes already present in the public timeline and recruit early sensors.

## Reddit — r/vibecoding / r/ClaudeCode / r/codex / r/aiagents

Suggested title:

**I got tired of guessing when AI coding quotas reset, so I built a cross-provider quota radar**

Body:

I keep bouncing between coding agents and the quota UX is surprisingly fragmented. A limit can reset, tighten or change policy and you usually discover it only after your workflow breaks.

I built VibeLimits as a small open-source radar for that problem. It tracks official provider changes and can crowd-confirm unexpected resets from privacy-preserving local sensors.

The important bit: a normal scheduled personal reset does **not** become a global alert. An unexpected reset starts as detected and needs three independent installations before it becomes confirmed.

The sensor sends a random installation UUID and quota-window numbers only. No prompts, code, repository contents, hostname or account identity.

Current registry includes Codex, Claude Code, Cursor, Windsurf, Gemini CLI, Copilot, Kiro, Zed, OpenCode, Amp, Cline, Roo Code and GitHub Spark.

Live radar: https://heocjdyufceudxdbghck.supabase.co/functions/v1/vibelimits-api

GitHub: https://github.com/ctmakc/vibelimits

I mainly need early sensor coverage now. If you use one of these tools heavily, feedback on the reset detection would be useful.

### Community adaptation

- `r/codex`: lead with Codex and the 3-sensor reset logic.
- `r/ClaudeCode`: lead with five-hour / weekly limit confusion and privacy.
- `r/vibecoding`: lead with multi-tool workflow and quota interruptions.
- `r/aiagents`: lead with architecture, correlation and source adapters.
- `r/buildinpublic`: lead with how the product was validated and what early telemetry will decide.

Do not cross-post identical text at the same time. Rewrite the first paragraph and title for each community.

## Telegram / Discord communities

Short version:

**VibeLimits — live quota radar for AI coding agents**

Codex / Claude Code / Cursor / Windsurf / Gemini CLI / Copilot + more in one feed. Official limit changes plus crowd-confirmed unexpected resets.

A reset needs 3 independent sensors before it is called global. Sensor is open source and sends quota windows + random install ID only — no prompts/code/account identity.

Live: https://heocjdyufceudxdbghck.supabase.co/functions/v1/vibelimits-api
GitHub: https://github.com/ctmakc/vibelimits

We need early sensor coverage more than stars. Heavy users welcome.

## Facebook / local tech groups

Suggested copy:

Built a small open-source utility for people who use several AI coding agents every day: VibeLimits watches quota resets, limit changes and provider policy changes in one place.

The interesting part is crowd confirmation. It deliberately ignores ordinary personal scheduled resets and only marks an unexpected reset as global after independent installations see the same drop.

No prompts or source code are collected.

Live radar: https://heocjdyufceudxdbghck.supabase.co/functions/v1/vibelimits-api
Source: https://github.com/ctmakc/vibelimits

Looking for developers who use Codex / Claude Code / Cursor heavily and are willing to run the sensor.

## Product Hunt

Tagline:

**The quota radar for AI coding agents**

One-liner:

Track official quota changes and crowd-confirmed unexpected resets across the AI coding tools you actually use.

First comment themes:

- why quota opacity is expensive during long coding sessions;
- why personal scheduled resets are filtered out;
- why three independent sensors are required;
- privacy model;
- open-source sensor;
- roadmap: richer provider adapters, Discord/webhooks, historical analytics and forecasting.

Wait until there is at least one genuine crowd-confirmed event or meaningful sensor coverage before making Product Hunt a major launch.

## Hacker News

Do not use polished promotional copy or coordinate votes/comments.

Post only when the live service is actually usable and keep the submission factual. Suggested facts to write in your own words:

- problem: coding-agent quotas are provider-specific and difficult to observe;
- implementation: Supabase/Postgres event store + Edge API + Python local sensor;
- correlation: unexpected drop from >=55% used to <=15%, >=50 percentage-point drop;
- scheduled reset tolerance: 25 minutes around expected reset time;
- global threshold: 3 unique sensors;
- privacy: no prompts/source/account identity;
- repository and live demo links;
- what you want feedback on: false positives, provider adapters and reset semantics.

## Habr / technical article

Working title:

**Как мы отличаем глобальный reset лимитов AI coding agents от обычного персонального reset**

Outline:

1. Why quota tracking is harder than it looks.
2. Different provider quota models.
3. Why scraping account identity is the wrong architecture.
4. Normalized quota-window schema.
5. Reset correlation algorithm.
6. False-positive suppression.
7. Privacy threat model.
8. Supabase/Postgres production architecture.
9. Open-source sensor.
10. What data will improve the model next.

## V2EX / Chinese communities

Use a technical discussion rather than an advertisement. Some nodes prohibit traffic-diversion / promotional posts.

Lead with the engineering problem: distinguishing an actual provider-wide reset from a user's scheduled reset. Include architecture snippets and only link the project where community rules permit it.

## First paid test

Do not run broad Meta acquisition yet. Paid traffic is useful only after the page shows live evidence and sensor onboarding is frictionless.

Initial experiment budget: **$200–500 total**.

Priority:

1. niche Telegram / Discord developer communities;
2. newsletter or community placements for Claude Code / Codex users;
3. small Reddit tests only where community/ad targeting is precise;
4. retarget visitors later if meaningful traffic exists.

Primary early KPI is **active sensor installations**, not page views or GitHub stars.

## Launch checklist

- [x] public repository;
- [x] production database;
- [x] production Edge API;
- [x] public dashboard;
- [x] historical official events;
- [x] sensor registration;
- [x] authenticated sensor submission;
- [x] 3-sensor reset confirmation logic;
- [x] privacy model documented;
- [x] one-command `--submit` flow;
- [ ] dedicated domain;
- [ ] public Telegram bot/channel token configured;
- [ ] first 10+ real sensor installations;
- [ ] first genuine confirmed reset;
- [ ] Product Hunt launch;
- [ ] broader paid acquisition.
