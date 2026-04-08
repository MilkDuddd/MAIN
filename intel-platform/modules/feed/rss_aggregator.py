"""RSS/Atom feed aggregator for geopolitical and intelligence news."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser

from core import database
from core.config import GEO_RSS_FEEDS, UAP_RSS_FEEDS
from models.feed import FeedItem

_ALL_FEEDS = {
    "geopolitical": GEO_RSS_FEEDS,
    "uap":          UAP_RSS_FEEDS,
}

_EXTRA_FEEDS: list[str] = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.ft.com/rss/home",
]


def fetch_feed(url: str, category: str = "general") -> list[FeedItem]:
    """Parse a single RSS/Atom feed."""
    try:
        feed = feedparser.parse(url)
        items: list[FeedItem] = []
        source_name = feed.feed.get("title", url)[:80]
        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            pub = entry.get("published_parsed")
            pub_str = None
            if pub:
                pub_str = datetime(*pub[:6], tzinfo=timezone.utc).isoformat()

            feed_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()
            items.append(FeedItem(
                feed_id=feed_id,
                source=source_name,
                title=title,
                url=link,
                published_at=pub_str,
                summary=summary[:500] if summary else None,
                category=category,
                collected_at=datetime.now(timezone.utc).isoformat(),
            ))
        return items
    except Exception:
        return []


def update_all_feeds() -> None:
    """Scheduled: fetch all configured RSS feeds and store items."""
    all_items: list[FeedItem] = []
    for category, urls in _ALL_FEEDS.items():
        for url in urls:
            all_items.extend(fetch_feed(url, category))
    for url in _EXTRA_FEEDS:
        all_items.extend(fetch_feed(url, "general"))
    _save_items(all_items)


def _save_items(items: list[FeedItem]) -> None:
    rows = [
        (
            item.feed_id, item.source, item.title, item.url, item.published_at,
            item.summary, item.category, None, item.collected_at,
        )
        for item in items
    ]
    if rows:
        database.execute_many(
            """INSERT OR IGNORE INTO feed_items
            (feed_id, source, title, url, published_at, summary, category, matched_keywords, collected_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            rows,
        )


def get_recent(category: Optional[str] = None, days: int = 3, limit: int = 100) -> list[FeedItem]:
    """Retrieve recent feed items from the database."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    if category:
        rows = database.execute(
            "SELECT * FROM feed_items WHERE category=? AND published_at >= ? ORDER BY published_at DESC LIMIT ?",
            (category, cutoff, limit),
        )
    else:
        rows = database.execute(
            "SELECT * FROM feed_items WHERE published_at >= ? ORDER BY published_at DESC LIMIT ?",
            (cutoff, limit),
        )
    return [
        FeedItem(
            feed_id=r["feed_id"], source=r["source"], title=r["title"],
            url=r["url"], published_at=r["published_at"], summary=r["summary"],
            category=r["category"], collected_at=r["collected_at"],
        )
        for r in rows
    ]
