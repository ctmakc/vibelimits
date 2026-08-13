from __future__ import annotations

import asyncio
import html

import httpx

from .config import settings
from .providers import PROVIDERS
from .state import EventRecord, store


class TelegramService:
    def __init__(self):
        self.offset = 0

    @property
    def enabled(self) -> bool:
        return bool(settings.telegram_bot_token)

    async def api(self, method: str, **payload):
        if not self.enabled:
            return None
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/{method}"
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json().get("result")

    async def send(self, recipient_id: str, text: str) -> None:
        try:
            await self.api("sendMessage", chat_id=recipient_id, text=text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception:
            pass

    def format_event(self, e: EventRecord) -> str:
        icon = {
            "quota_reset": "🔥", "quota_increase": "🚀", "quota_decrease": "⚠️",
            "promo_credit": "🎁", "outage_compensation": "🛠", "policy_change": "📡",
            "personal_reset": "✅",
        }.get(e.event_type, "📡")
        confidence = {"official": "OFFICIAL", "confirmed": "CONFIRMED", "detected": "DETECTED"}.get(e.confidence, e.confidence.upper())
        source = f'\n<a href="{html.escape(e.source_url)}">source</a>' if e.source_url else ""
        return f"{icon} <b>{html.escape(e.title)}</b>\n{html.escape(e.summary)}\n\n<b>{confidence}</b> · evidence: {e.evidence_count}{source}"

    async def dispatch_pending(self) -> None:
        if not self.enabled:
            return
        for e in store.pending_events():
            recipients: set[str] = set()
            if settings.telegram_channel_id and e.event_type != "personal_reset":
                recipients.add(settings.telegram_channel_id)
            if e.event_type != "personal_reset":
                for recipient_id, sub in store.active_subscriptions().items():
                    filt = sub.get("provider_filters") or []
                    if not filt or e.provider in filt:
                        recipients.add(recipient_id)
            for recipient_id in recipients:
                await self.send(recipient_id, self.format_event(e))
            store.mark_dispatched(e.fingerprint)

    async def _handle_command(self, recipient_id: str, text: str) -> None:
        command, *rest = text.strip().split(maxsplit=1)
        arg = rest[0] if rest else ""
        sub = store.get_subscription(recipient_id)
        if command in ("/start", "/all"):
            filters = [] if command == "/all" else (sub or {}).get("provider_filters", [])
            store.set_subscription(recipient_id, True, filters)
            await self.send(recipient_id, "✅ Alerts enabled. Use <code>/only codex,claude_code,cursor</code> to filter.")
        elif command == "/stop":
            store.set_subscription(recipient_id, False)
            await self.send(recipient_id, "Alerts disabled. /start to resume.")
        elif command == "/only":
            requested = [x.strip() for x in arg.split(",") if x.strip()]
            valid = [x for x in requested if x in PROVIDERS]
            store.set_subscription(recipient_id, True, valid)
            await self.send(recipient_id, "Tracking: " + (", ".join(valid) if valid else "all providers"))
        elif command == "/providers":
            lines = [f"<code>{p.id}</code> — {html.escape(p.name)}" for p in PROVIDERS.values()]
            await self.send(recipient_id, "<b>Providers</b>\n" + "\n".join(lines))
        elif command == "/status":
            if not sub or not sub.get("enabled"):
                await self.send(recipient_id, "Alerts: OFF")
            else:
                filt = ", ".join(sub.get("provider_filters") or []) or "all providers"
                await self.send(recipient_id, f"Alerts: ON\nProviders: {html.escape(filt)}")
        elif command == "/latest":
            events = store.list_events(limit=1)
            await self.send(recipient_id, self.format_event(events[0]) if events else "No confirmed events yet.")
        else:
            await self.send(recipient_id, "Commands: /start /stop /status /providers /only /all /latest")

    async def poll_updates_once(self) -> None:
        if not self.enabled:
            return
        try:
            updates = await self.api("getUpdates", offset=self.offset, timeout=20, allowed_updates=["message"])
            for update in updates or []:
                self.offset = max(self.offset, update["update_id"] + 1)
                msg = update.get("message") or {}
                text = msg.get("text", "")
                recipient_id = str((msg.get("chat") or {}).get("id", ""))
                if recipient_id and text.startswith("/"):
                    await self._handle_command(recipient_id, text)
        except Exception:
            await asyncio.sleep(5)

    async def run(self) -> None:
        while True:
            await self.poll_updates_once()
            await self.dispatch_pending()
            await asyncio.sleep(2)
