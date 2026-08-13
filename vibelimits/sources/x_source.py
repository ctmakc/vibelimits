from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..config import settings
from ..schemas import Announcement


class XSource:
    def __init__(self, engine):
        self.engine = engine
        self.user_ids: dict[str, tuple[str, str]] = {}

    async def _resolve_users(self, client: httpx.AsyncClient) -> None:
        pairs = [(provider, username) for provider, users in settings.provider_x_handles.items() for username in users]
        usernames = sorted({username for _, username in pairs})
        for index in range(0, len(usernames), 100):
            batch = usernames[index:index + 100]
            if not batch:
                continue
            response = await client.get("https://api.x.com/2/users/by", params={"usernames": ",".join(batch)})
            response.raise_for_status()
            by_name = {item["username"].lower(): item["id"] for item in response.json().get("data", [])}
            for provider, username in pairs:
                user_id = by_name.get(username.lower())
                if user_id:
                    self.user_ids[username.lower()] = (user_id, provider)

    async def poll_once(self) -> None:
        if not settings.x_bearer_token:
            return
        headers = {"Authorization": f"Bearer {settings.x_bearer_token}"}
        async with httpx.AsyncClient(headers=headers, timeout=20) as client:
            if not self.user_ids:
                await self._resolve_users(client)
            for username, (user_id, provider) in list(self.user_ids.items()):
                try:
                    response = await client.get(
                        f"https://api.x.com/2/users/{user_id}/tweets",
                        params={"max_results": 10, "exclude": "retweets,replies", "tweet.fields": "created_at"},
                    )
                    response.raise_for_status()
                    for tweet in reversed(response.json().get("data", [])):
                        created = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")) if tweet.get("created_at") else datetime.now(timezone.utc)
                        await self.engine.ingest_announcement(Announcement(
                            provider=provider,
                            source=f"x:@{username}",
                            source_ref=tweet["id"],
                            text=tweet.get("text", ""),
                            published_at=created,
                            url=f"https://x.com/{username}/status/{tweet['id']}",
                            official=True,
                        ))
                except Exception:
                    continue
