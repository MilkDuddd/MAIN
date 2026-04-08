"""UAP news aggregation from RSS feeds and NewsAPI."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser

from core import database, http_client, settings
from core.config import UAP_RSS_FEEDS, UAP_KEYWORDS, NEWSAPI_URL
from models.uap import UAPNewsItem, UAPNewsResult


def _matches_uap(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in UAP_KEYWORDS if kw.lower() in text_lower]


def fetch_rss_uap(days: int = 7) -> list[UAPNewsItem]:
    """Pull UAP-tagged articles from RSS feeds."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items: list[UAPNewsItem] = []
    for feed_url in UAP_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                combined = f"{title} {summary}"
                matched = _matches_uap(combined)
                if not matched:
                    continue
                pub = entry.get("published_parsed")
                if pub:
                    pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue
                    pub_str = pub_dt.isoformat()
                else:
                    pub_str = None
                items.append(UAPNewsItem(
                    title=title,
                    source=feed.feed.get("title", feed_url),
                    published_at=pub_str,
                    url=entry.get("link"),
                    summary=summary[:500] if summary else None,
                    matched_keywords=matched,
                ))
        except Exception:
            continue
    return items


def fetch_newsapi_uap(days: int = 7) -> list[UAPNewsItem]:
    """Fetch UAP news via NewsAPI.org."""
    key = settings.get("newsapi_key", "")
    if not key:
        return []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        resp = http_client.get(
            f"{NEWSAPI_URL}/everything",
            params={
                "q": "UAP OR UFO OR \"unidentified aerial\" OR \"non-human intelligence\"",
                "from": cutoff,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 100,
                "apiKey": key,
            },
            source="NewsAPI",
            timeout=30,
        )
        articles = resp.json().get("articles", [])
        items: list[UAPNewsItem] = []
        for art in articles:
            title = art.get("title", "")
            desc = art.get("description", "") or ""
            matched = _matches_uap(f"{title} {desc}")
            items.append(UAPNewsItem(
                title=title,
                source=art.get("source", {}).get("name", "NewsAPI"),
                published_at=art.get("publishedAt"),
                url=art.get("url"),
                summary=desc[:500],
                matched_keywords=matched,
            ))
        return items
    except Exception:
        return []


def update_uap_news() -> None:
    """Scheduled: fetch and store recent UAP news."""
    items = fetch_rss_uap(days=1) + fetch_newsapi_uap(days=1)
    _save_items(items)


def _save_items(items: list[UAPNewsItem]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = []
    for item in items:
        feed_id = hashlib.md5(f"{item.title}{item.url}".encode()).hexdigest()
        rows.append((
            feed_id, item.source, item.title, item.url, item.published_at,
            item.summary, "uap", str(item.matched_keywords), now,
        ))
    if rows:
        database.execute_many(
            """INSERT OR IGNORE INTO feed_items
            (feed_id, source, title, url, published_at, summary, category, matched_keywords, collected_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            rows,
        )


def search_db(days: int = 7, keyword: Optional[str] = None) -> UAPNewsResult:
    """Query cached UAP news from the database."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    if keyword:
        rows = database.execute(
            """SELECT * FROM feed_items WHERE category='uap'
               AND published_at >= ? AND (title LIKE ? OR summary LIKE ?)
               ORDER BY published_at DESC LIMIT 200""",
            (cutoff, f"%{keyword}%", f"%{keyword}%"),
        )
    else:
        rows = database.execute(
            "SELECT * FROM feed_items WHERE category='uap' AND published_at >= ? ORDER BY published_at DESC LIMIT 200",
            (cutoff,),
        )
    items = [
        UAPNewsItem(
            title=r["title"], source=r["source"],
            published_at=r["published_at"], url=r["url"],
            summary=r["summary"],
        )
        for r in rows
    ]
    return UAPNewsResult(days_filter=days, items=items, total=len(items))
