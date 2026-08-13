from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _json(name: str, default: Any) -> Any:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


DEFAULT_X_HANDLES = {
    "codex": ["OpenAIDevs", "OpenAI"],
    "claude_code": ["AnthropicAI"],
    "cursor": ["cursor_ai"],
    "windsurf": ["windsurf"],
    "gemini_cli": ["GoogleAI", "GoogleDeepMind"],
    "copilot": ["github"],
    "kiro": ["kirodotdev"],
    "zed": ["zeddotdev"],
    "opencode": ["opencode"],
    "amp": ["sourcegraph"],
}

DEFAULT_FEEDS = {
    "codex": ["https://github.com/openai/codex/releases.atom"],
    "gemini_cli": ["https://github.com/google-gemini/gemini-cli/releases.atom"],
}


@dataclass(slots=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./vibelimits.db"))
    public_base_url: str = field(default_factory=lambda: os.getenv("PUBLIC_BASE_URL", "http://localhost:8080"))
    admin_token: str = field(default_factory=lambda: os.getenv("ADMIN_TOKEN", ""))
    sensor_shared_secret: str = field(default_factory=lambda: os.getenv("SENSOR_SHARED_SECRET", ""))
    poll_interval_seconds: int = field(default_factory=lambda: _int("POLL_INTERVAL_SECONDS", 60))
    global_confirm_sensor_count: int = field(default_factory=lambda: _int("GLOBAL_CONFIRM_SENSOR_COUNT", 3))
    global_reset_drop_percent: int = field(default_factory=lambda: _int("GLOBAL_RESET_DROP_PERCENT", 50))
    expected_reset_tolerance_minutes: int = field(default_factory=lambda: _int("EXPECTED_RESET_TOLERANCE_MINUTES", 25))
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_channel_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHANNEL_ID", ""))
    x_bearer_token: str = field(default_factory=lambda: os.getenv("X_BEARER_TOKEN", ""))
    provider_x_handles: dict[str, list[str]] = field(default_factory=lambda: _json("PROVIDER_X_HANDLES_JSON", DEFAULT_X_HANDLES))
    provider_feeds: dict[str, list[str]] = field(default_factory=lambda: _json("PROVIDER_FEEDS_JSON", DEFAULT_FEEDS))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", ""))
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", ""))


settings = Settings()
