"""Conflict event monitoring via ACLED API and ReliefWeb."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from core import database, http_client, settings
from core.config import ACLED_API, RELIEFWEB_API
from models.geopolitical import ConflictEvent, ConflictResult


def fetch_acled(country: Optional[str] = None, days: int = 30) -> list[ConflictEvent]:
    """Fetch conflict events from ACLED API."""
    email = settings.get("acled_email", "")
    key = settings.get("acled_key", "")
    if not email or not key:
        return []

    params: dict = {
        "email": email,
        "key": key,
        "limit": 500,
        "fields": "event_id_cnty|event_date|event_type|country|region|location|latitude|longitude|actor1|actor2|fatalities|notes|source_url",
    }
    if country:
        params["country"] = country
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    params["event_date"] = cutoff
    params["event_date_where"] = ">="

    try:
        resp = http_client.get(ACLED_API, params=params, source="ACLED", timeout=60)
        data = resp.json().get("data", [])
        events: list[ConflictEvent] = []
        for d in data:
            events.append(ConflictEvent(
                event_id=f"ACLED-{d.get('event_id_cnty', hashlib.md5(str(d).encode()).hexdigest()[:8])}",
                source="ACLED",
                event_date=d.get("event_date"),
                country=d.get("country"),
                region=d.get("region"),
                location=d.get("location"),
                latitude=_safe_float(d.get("latitude")),
                longitude=_safe_float(d.get("longitude")),
                event_type=d.get("event_type"),
                actor1=d.get("actor1"),
                actor2=d.get("actor2"),
                fatalities=_safe_int(d.get("fatalities")),
                notes=d.get("notes"),
                source_url=d.get("source_url"),
            ))
        return events
    except Exception:
        return []


def fetch_reliefweb(country: Optional[str] = None, days: int = 30) -> list[ConflictEvent]:
    """Fetch crisis updates from ReliefWeb API."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    params: dict = {
        "appname": "intel-platform",
        "limit": 200,
        "fields[include][]": ["title", "date", "country", "source"],
        "filter[field]": "date.created",
        "filter[value][from]": cutoff,
        "sort[]": "date.created:desc",
    }
    if country:
        params["filter[conditions][0][field]"] = "country.name"
        params["filter[conditions][0][value]"] = country

    try:
        resp = http_client.get(
            f"{RELIEFWEB_API}/reports",
            params=params,
            source="ReliefWeb",
            timeout=45,
        )
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


def _safe_float(v) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _safe_int(v) -> Optional[int]:
    try:
        return int(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def update_conflicts() -> None:
    """Scheduled job: refresh conflict events."""
    now = datetime.now(timezone.utc).isoformat()
    events = fetch_acled(days=3) + fetch_reliefweb(days=3)
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
