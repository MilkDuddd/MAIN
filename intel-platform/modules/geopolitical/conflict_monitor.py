"""Conflict event monitoring via GDELT and ReliefWeb — no API keys required."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from core import database, http_client
from core.config import GDELT_API, RELIEFWEB_API
from models.geopolitical import ConflictEvent, ConflictResult


def fetch_gdelt_conflicts(country: Optional[str] = None, days: int = 30) -> list[ConflictEvent]:
    """Fetch conflict/violence events from GDELT — free, no key required."""
    query = "conflict violence war protest coup"
    if country:
        query = f"{country} {query}"
    params = {
        "query":      query,
        "mode":       "ArtList",
        "maxrecords": "100",
        "format":     "json",
        "timespan":   f"{days}d",
    }
    try:
        resp = http_client.get(GDELT_API, params=params, source="GDELT", timeout=45)
        articles = resp.json().get("articles", [])
        events: list[ConflictEvent] = []
        for a in articles:
            seen = (a.get("seendate") or "")[:8]
            try:
                event_date = datetime.strptime(seen, "%Y%m%d").strftime("%Y-%m-%d") if seen else None
            except ValueError:
                event_date = None
            eid = f"GDELT-{hashlib.md5(a.get('url', str(a)).encode()).hexdigest()[:12]}"
            events.append(ConflictEvent(
                event_id=eid,
                source="GDELT",
                event_date=event_date,
                country=a.get("sourcecountry"),
                notes=a.get("title"),
                source_url=a.get("url"),
            ))
        return events
    except Exception:
        return []


def fetch_reliefweb(country: Optional[str] = None, days: int = 30) -> list[ConflictEvent]:
    """Fetch crisis updates from ReliefWeb — free, no key required."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    params: dict = {
        "appname":              "intel-platform",
        "limit":                200,
        "fields[include][]":    ["title", "date", "country", "source"],
        "filter[field]":        "date.created",
        "filter[value][from]":  cutoff,
        "sort[]":               "date.created:desc",
    }
    if country:
        params["filter[conditions][0][field]"] = "country.name"
        params["filter[conditions][0][value]"] = country

    try:
        resp = http_client.get(f"{RELIEFWEB_API}/reports", params=params,
                               source="ReliefWeb", timeout=45)
        data = resp.json().get("data", [])
        events: list[ConflictEvent] = []
        for d in data:
            flds = d.get("fields", {})
            eid = f"RW-{d.get('id', hashlib.md5(str(d).encode()).hexdigest()[:8])}"
            countries = flds.get("country", [{}])
            country_name = countries[0].get("name") if countries else None
            events.append(ConflictEvent(
                event_id=eid,
                source="ReliefWeb",
                event_date=flds.get("date", {}).get("created", "")[:10],
                country=country_name,
                notes=flds.get("title"),
            ))
        return events
    except Exception:
        return []


def update_conflicts() -> None:
    """Scheduled job: refresh conflict events from GDELT + ReliefWeb."""
    now = datetime.now(timezone.utc).isoformat()
    events = fetch_gdelt_conflicts(days=3) + fetch_reliefweb(days=3)
    if not events:
        return
    rows = [
        (
            e.event_id, e.source, e.event_date, e.country, e.region,
            e.location, e.latitude, e.longitude, e.event_type,
            e.actor1, e.actor2, e.fatalities, e.notes, e.source_url, now,
        )
        for e in events
    ]
    database.execute_many(
        """INSERT OR IGNORE INTO conflict_events
        (event_id, source, event_date, country, region, location, latitude, longitude,
         event_type, actor1, actor2, fatalities, notes, source_url, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(country: Optional[str] = None, days: int = 30) -> ConflictResult:
    """Query cached conflict events from the database."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    if country:
        rows = database.execute(
            "SELECT * FROM conflict_events WHERE country LIKE ? AND event_date >= ? ORDER BY event_date DESC LIMIT 500",
            (f"%{country}%", cutoff),
        )
    else:
        rows = database.execute(
            "SELECT * FROM conflict_events WHERE event_date >= ? ORDER BY event_date DESC LIMIT 500",
            (cutoff,),
        )
    events = [
        ConflictEvent(
            event_id=r["event_id"], source=r["source"], event_date=r["event_date"],
            country=r["country"], region=r["region"], location=r["location"],
            latitude=r["latitude"], longitude=r["longitude"], event_type=r["event_type"],
            actor1=r["actor1"], actor2=r["actor2"], fatalities=r["fatalities"],
            notes=r["notes"], source_url=r["source_url"],
        )
        for r in rows
    ]
    return ConflictResult(country_filter=country, events=events, total=len(events))
