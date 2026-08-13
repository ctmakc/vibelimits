from __future__ import annotations

import argparse
import asyncio

from .engine import EventEngine
from .sources.feed_source import FeedSource
from .sources.x_source import XSource
from .state import store
from .telegram import TelegramService


async def run(interval: int) -> None:
    engine = EventEngine(store)
    feeds = FeedSource(engine)
    x_source = XSource(engine)
    telegram = TelegramService()
    while True:
        await feeds.poll_once()
        await x_source.poll_once()
        await telegram.poll_updates_once()
        await telegram.dispatch_pending()
        await asyncio.sleep(interval)


def cli() -> None:
    parser = argparse.ArgumentParser(description="VibeLimits collector and delivery worker")
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()
    asyncio.run(run(args.interval))


if __name__ == "__main__":
    cli()
