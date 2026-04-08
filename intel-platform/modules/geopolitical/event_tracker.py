"""GDELT Project event stream for live political events."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from core import database, http_client
from core.config import GDELT_API
from models.geopolitical import PoliticalEvent, EventsResult


def _build_query(country: Optional[str] = None, days: int = 7, max_results: int = 250) -> dict:
    query = "sourcelang:english"
    if country:
        query = f"{country} {query}"
    return {
        "query": query,
        "mode": "ArtList",
        "maxrecords": max_results,
        "timespan": f"{days}d",
        "format": "json",
        "sort": "DateDesc",
    }


def fetch_events(country: Optional[str] = None, days: int = 7) -> EventsResult:
    """Fetch recent political events from GDELT."""
    try:
        params = _build_query(country, days)
        resp = http_client.get(GDELT_API, params=params, source="GDELT", timeout=45)
        data = resp.json()
        articles = data.get("articles", [])
        events: list[PoliticalEvent] = []
        for art in articles:
            url = art.get("url", "")
            event_id = hashlib.md5(url.encode()).hexdigest()
            events.append(PoliticalEvent(
                event_id=event_id,
                source="GDELT",
                event_date=art.get("seendate", "")[:8],
                actor1=art.get("domain"),
                actor1_country=art.get("sourcecountry"),
                event_description=art.get("title"),
                action_type=art.get("language"),
                source_url=url,
            ))
        return EventsResult(
            query=country or "global",
            events=events,
            total=len(events),
        )
    except Exception as e:
        return EventsResult(query=country or "global", error=str(e))


def update_gdelt_events() -> None:
    """Scheduled job: pull latest GDELT events into the database."""
    result = fetch_events(days=1)
    if result.error or not result.events:
        return
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            e.event_id, "GDELT", e.event_date, e.actor1, e.actor1_country,
            e.actor2, e.actor2_country, e.event_description,
            e.action_type, e.goldstein_scale, e.source_url, now,
        )
        for e in result.events
    ]
    database.execute_many(
        """INSERT OR IGNORE INTO political_events
        (event_id, source, event_date, actor1, actor1_country, actor2, actor2_country,
         event_description, action_type, goldstein_scale, source_url, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(country: Optional[str] = None, days: int = 7) -> EventsResult:
    """Query cached GDELT events from the database."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y%m%d")
    if country:
        rows = database.execute(
            """SELECT * FROM political_events
               WHERE (actor1_country LIKE ? OR event_description LIKE ?)
               AND event_date >= ? ORDER BY event_date DESC LIMIT 500""",
            (f"%{country}%", f"%{country}%", cutoff),
        )
    else:
        rows = database.execute(
            "SELECT * FROM political_events WHERE event_date >= ? ORDER BY event_date DESC LIMIT 500",
            (cutoff,),
        )
    events = [
        PoliticalEvent(
            event_id=r["event_id"],
            source=r["source"],
            event_date=r["event_date"],
            actor1=r["actor1"],
            actor1_country=r["actor1_country"],
            actor2=r["actor2"],
            actor2_country=r["actor2_country"],
            event_description=r["event_description"],
            action_type=r["action_type"],
            goldstein_scale=r["goldstein_scale"],
            source_url=r["source_url"],
        )
        for r in rows
    ]
    return EventsResult(query=country or "global", events=events, total=len(events))
