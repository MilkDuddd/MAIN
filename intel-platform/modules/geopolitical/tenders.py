"""Government contract/tender tracking — SAM.gov (US) and ReliefWeb."""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from core import database, http_client, settings
from core.config import SAM_GOV_API
from models.geopolitical import Tender, TenderResult


def fetch_sam_gov(keyword: str = "", days: int = 30) -> list[Tender]:
    """Fetch US federal contract opportunities from SAM.gov."""
    key = settings.get("sam_gov_key", "")
    if not key:
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%m/%d/%Y")
    params = {
        "api_key": key,
        "postedFrom": cutoff,
        "limit": 250,
        "offset": 0,
        "ptype": "o",  # opportunities
    }
    if keyword:
        params["keywords"] = keyword

    try:
        resp = http_client.get(SAM_GOV_API, params=params, source="SAM.gov", timeout=60)
        data = resp.json()
        opps = data.get("opportunitiesData", [])
        tenders: list[Tender] = []
        for opp in opps:
            tenders.append(Tender(
                tender_id=f"SAM-{opp.get('noticeId', '')}",
                source="SAM.gov",
                title=opp.get("title"),
                description=opp.get("description"),
                agency=opp.get("fullParentPathName"),
                country="US",
                published_date=opp.get("postedDate"),
                deadline_date=opp.get("responseDeadLine"),
                naics_code=opp.get("naicsCode"),
                url=opp.get("uiLink"),
            ))
        return tenders
    except Exception:
        return []


def update_tenders() -> None:
    """Scheduled job: refresh government tenders."""
    now = datetime.now(timezone.utc).isoformat()
    tenders = fetch_sam_gov(days=7)
    if not tenders:
        return
    rows = [
        (
            t.tender_id, t.source, t.title, t.description, t.agency, t.country,
            t.published_date, t.deadline_date, t.estimated_value_usd,
            t.award_status, t.awardee, t.naics_code, t.url, now,
        )
        for t in tenders
    ]
    database.execute_many(
        """INSERT OR IGNORE INTO government_tenders
        (tender_id, source, title, description, agency, country, published_date,
         deadline_date, estimated_value_usd, award_status, awardee, naics_code, url, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(keyword: str = "", country: Optional[str] = None, days: int = 30) -> TenderResult:
    """Query cached tenders from the database."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    q = f"%{keyword}%"
    if country:
        rows = database.execute(
            """SELECT * FROM government_tenders
               WHERE (title LIKE ? OR description LIKE ?) AND country LIKE ? AND published_date >= ?
               ORDER BY published_date DESC LIMIT 200""",
            (q, q, f"%{country}%", cutoff),
        )
    else:
        rows = database.execute(
            """SELECT * FROM government_tenders
               WHERE (title LIKE ? OR description LIKE ?) AND published_date >= ?
               ORDER BY published_date DESC LIMIT 200""",
            (q, q, cutoff),
        )
    tenders = [
        Tender(
            tender_id=r["tender_id"], source=r["source"], title=r["title"],
            description=r["description"], agency=r["agency"], country=r["country"],
            published_date=r["published_date"], deadline_date=r["deadline_date"],
            estimated_value_usd=r["estimated_value_usd"], naics_code=r["naics_code"],
            url=r["url"],
        )
        for r in rows
    ]
    return TenderResult(query=keyword or country or "all", tenders=tenders, total=len(tenders))
