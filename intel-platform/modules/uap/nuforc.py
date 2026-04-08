"""NUFORC (National UFO Reporting Center) sighting database scraper."""

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from bs4 import BeautifulSoup

from core import database, http_client
from core.config import NUFORC_BASE
from models.uap import UAPSighting, SightingsResult

# NUFORC publishes sightings by state and by event date
_STATE_CODES = [
    "AK","AL","AR","AZ","CA","CO","CT","DC","DE","FL","GA","HI","IA","ID",
    "IL","IN","KS","KY","LA","MA","MD","ME","MI","MN","MO","MS","MT","NC",
    "ND","NE","NH","NJ","NM","NV","NY","OH","OK","OR","PA","RI","SC","SD",
    "TN","TX","UT","VA","VT","WA","WI","WV","WY",
]


def _parse_table(html: str, source_url: str, state: Optional[str] = None) -> list[UAPSighting]:
    sightings: list[UAPSighting] = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"border": "1"}) or soup.find("table")
        if not table:
            return sightings
        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) < 5:
                continue
            # Typical NUFORC columns: Date/Time, City, State, Shape, Duration, Summary, Posted
            occurred = cells[0] if len(cells) > 0 else None
            city     = cells[1] if len(cells) > 1 else None
            st       = cells[2] if len(cells) > 2 else state
            shape    = cells[3] if len(cells) > 3 else None
            duration = cells[4] if len(cells) > 4 else None
            desc     = cells[5] if len(cells) > 5 else None
            posted   = cells[6] if len(cells) > 6 else None

            # Parse duration to seconds
            dur_sec = None
            if duration:
                m = re.search(r"(\d+)\s*(hour|hr|minute|min|second|sec)", duration.lower())
                if m:
                    n, unit = int(m.group(1)), m.group(2)
                    if "hour" in unit or "hr" in unit:
                        dur_sec = n * 3600
                    elif "min" in unit:
                        dur_sec = n * 60
                    else:
                        dur_sec = n

            report_id = hashlib.md5(f"{occurred}{city}{st}{desc}".encode()).hexdigest()[:12]
            # find detail link
            link = row.find("a")
            detail_url = f"{NUFORC_BASE}/{link['href']}" if link and link.get("href") else source_url

            sightings.append(UAPSighting(
                report_id=report_id,
                source="NUFORC",
                occurred_date=occurred,
                reported_date=posted,
                city=city,
                state=st,
                country="US",
                shape=shape,
                duration_sec=dur_sec,
                description=desc,
                posted_url=detail_url,
            ))
    except Exception:
        pass
    return sightings


def fetch_by_state(state: str) -> list[UAPSighting]:
    """Scrape NUFORC sightings for a given US state code."""
    url = f"{NUFORC_BASE}/ndxloc.html"
    try:
        resp = http_client.get(url, source="NUFORC", timeout=30)
        soup = BeautifulSoup(resp.text, "html.parser")
        # Find state link
        state_link = None
        for a in soup.find_all("a"):
            href = a.get("href", "")
            text = a.get_text(strip=True).upper()
            if text == state.upper() or state.upper() in href.upper():
                state_link = href
                break
        if not state_link:
            return []
        if not state_link.startswith("http"):
            state_link = f"{NUFORC_BASE}/{state_link.lstrip('/')}"
        resp2 = http_client.get(state_link, source="NUFORC", timeout=30)
        return _parse_table(resp2.text, state_link, state)
    except Exception:
        return []


def fetch_recent(days: int = 30) -> list[UAPSighting]:
    """Fetch recent NUFORC reports from the 'latest' page."""
    url = f"{NUFORC_BASE}/ndxevent.html"
    try:
        resp = http_client.get(url, source="NUFORC", timeout=30)
        return _parse_table(resp.text, url)
    except Exception:
        return []


def update_nuforc_recent() -> None:
    """Scheduled: pull recent NUFORC sightings."""
    sightings = fetch_recent(days=7)
    _save_sightings(sightings)


def _save_sightings(sightings: list[UAPSighting]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            s.report_id, "NUFORC", s.occurred_date, s.reported_date,
            s.city, s.state, s.country, s.shape, s.duration_sec,
            s.description, s.posted_url, None, None, now,
        )
        for s in sightings
    ]
    database.execute_many(
        """INSERT OR IGNORE INTO uap_sightings
        (report_id, source, occurred_date, reported_date, city, state, country,
         shape, duration_sec, description, posted_url, lat, lon, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(state: Optional[str] = None, days: Optional[int] = None, keyword: Optional[str] = None) -> SightingsResult:
    """Query cached NUFORC sightings from the database."""
    conditions = ["source='NUFORC'"]
    params: list = []
    if state:
        conditions.append("state=?")
        params.append(state.upper())
    if keyword:
        conditions.append("description LIKE ?")
        params.append(f"%{keyword}%")
    where = " AND ".join(conditions)
    rows = database.execute(
        f"SELECT * FROM uap_sightings WHERE {where} ORDER BY occurred_date DESC LIMIT 500",
        tuple(params),
    )
    sightings = [
        UAPSighting(
            report_id=r["report_id"], source=r["source"],
            occurred_date=r["occurred_date"], reported_date=r["reported_date"],
            city=r["city"], state=r["state"], country=r["country"],
            shape=r["shape"], duration_sec=r["duration_sec"],
            description=r["description"], posted_url=r["posted_url"],
            lat=r["lat"], lon=r["lon"],
        )
        for r in rows
    ]
    return SightingsResult(state_filter=state, days_filter=days, sightings=sightings, total=len(sightings))
