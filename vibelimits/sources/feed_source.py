from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from html import unescape
from xml.etree import ElementTree

import httpx

from ..config import settings
from ..schemas import Announcement


def _text(element) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def parse_feed(xml: str) -> list[dict]:
    root = ElementTree.fromstring(xml)
    items: list[dict] = []
    for entry in root.findall("{*}entry"):
        title = _text(entry.find("{*}title"))
        content = _text(entry.find("{*}content")) or _text(entry.find("{*}summary"))
        item_id = _text(entry.find("{*}id"))
        updated = _text(entry.find("{*}updated")) or _text(entry.find("{*}published"))
        link_element = entry.find("{*}link")
        link = link_element.attrib.get("href") if link_element is not None else None
        items.append({
            "id": item_id or link or hashlib.sha256((title + content).encode()).hexdigest(),
            "title": title,
            "text": content,
            "published": updated,
            "url": link,
        })
    for item in root.findall(".//item"):
        title = _text(item.find("title"))
        content = _text(item.find("description"))
        guid = _text(item.find("guid"))
        link = _text(item.find("link")) or None
        published = _text(item.find("pubDate"))
        items.append({
            "id": guid or link or hashlib.sha256((title + content).encode()).hexdigest(),
            "title": title,
            "text": content,
            "published": published,
            "url": link,
        })
    return items


def _parse_time(raw: str) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


class FeedSource:
    def __init__(self, engine):
        self.engine = engine

    async def poll_once(self) -> None:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for provider, urls in settings.provider_feeds.items():
                for url in urls:
                    try:
                        response = await client.get(url, headers={"User-Agent": "VibeLimits/0.1"})
                        response.raise_for_status()
                        for item in reversed(parse_feed(response.text)[-20:]):
                            await self.engine.ingest_announcement(Announcement(
                                provider=provider,
                                source=f"feed:{url}",
                                source_ref=str(item["id"]),
                                text=unescape(f"{item['title']} {item['text']}"),
                                published_at=_parse_time(item["published"]),
                                url=item.get("url"),
                                official=True,
                            ))
                    except Exception:
                        continue
