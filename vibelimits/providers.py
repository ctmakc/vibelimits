from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Provider:
    id: str
    name: str
    reset_model: str
    docs_url: str
    local_sensor: str


PROVIDERS: dict[str, Provider] = {
    "codex": Provider("codex", "OpenAI Codex", "rolling + weekly + promos", "https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan", "native"),
    "claude_code": Provider("claude_code", "Claude Code", "rolling + weekly", "https://support.anthropic.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan", "openusage"),
    "cursor": Provider("cursor", "Cursor", "monthly usage cycle", "https://docs.cursor.com/account/pricing", "openusage"),
    "windsurf": Provider("windsurf", "Windsurf", "monthly usage cycle", "https://docs.windsurf.com/windsurf/accounts/usage", "openusage"),
    "gemini_cli": Provider("gemini_cli", "Gemini CLI", "daily + model-specific", "https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/quota-and-pricing.md", "openusage"),
    "copilot": Provider("copilot", "GitHub Copilot", "calendar-month", "https://docs.github.com/en/copilot", "openusage"),
    "kiro": Provider("kiro", "Kiro", "provider-defined", "https://kiro.dev", "openusage"),
    "zed": Provider("zed", "Zed AI", "provider-defined", "https://zed.dev", "openusage"),
    "opencode": Provider("opencode", "OpenCode", "upstream-dependent", "https://opencode.ai", "openusage"),
    "amp": Provider("amp", "Amp", "provider-defined", "https://ampcode.com", "openusage"),
    "cline": Provider("cline", "Cline", "upstream-dependent", "https://cline.bot", "crowd"),
    "roo_code": Provider("roo_code", "Roo Code", "upstream-dependent", "https://roocode.com", "openusage"),
    "github_spark": Provider("github_spark", "GitHub Spark", "calendar-month", "https://github.com/features/spark", "crowd"),
}


def provider_ids() -> set[str]:
    return set(PROVIDERS)
