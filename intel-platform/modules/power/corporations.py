"""Corporate structure tracking via OpenCorporates API."""

import json
from datetime import datetime, timezone
from typing import Optional

from core import database, http_client
from core.config import OPENCORP_API
from models.power import Corporation, CorpResult


def fetch_company(name: str) -> CorpResult:
    """Search OpenCorporates for a company by name (public API, no key required)."""
    params: dict = {"q": name, "format": "json"}

    try:
        resp = http_client.get(
            f"{OPENCORP_API}/companies/search",
            params=params,
            source="OpenCorporates",
            timeout=30,
        )
        data = resp.json()
        results = data.get("results", {}).get("companies", [])
        corps: list[Corporation] = []
        for item in results:
            c = item.get("company", {})
            corps.append(Corporation(
                company_id=f"OC-{c.get('company_number', '')}-{c.get('jurisdiction_code', '')}",
                name=c.get("name", ""),
                jurisdiction=c.get("jurisdiction_code"),
                company_type=c.get("company_type"),
                incorporation_date=c.get("incorporation_date"),
                registered_address=_fmt_address(c.get("registered_address")),
                status=c.get("current_status"),
                source="OpenCorporates",
            ))
        return CorpResult(query=name, corporations=corps, total=len(corps))
    except Exception as e:
        return CorpResult(query=name, error=str(e))


def _fmt_address(addr: Optional[dict]) -> Optional[str]:
    if not addr:
        return None
    parts = [addr.get("street_address"), addr.get("locality"), addr.get("region"), addr.get("country")]
    return ", ".join(p for p in parts if p)


def save_to_db(corps: list[Corporation]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            c.company_id, c.name, c.jurisdiction, c.company_type,
            c.incorporation_date, c.registered_address, c.status,
            c.parent_company_id, json.dumps(c.officers), c.source, now,
        )
        for c in corps
    ]
    database.execute_many(
        """INSERT OR REPLACE INTO corporations
        (company_id, name, jurisdiction, company_type, incorporation_date,
         registered_address, status, parent_company_id, officers, source, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(name: str) -> CorpResult:
    rows = database.execute(
        "SELECT * FROM corporations WHERE name LIKE ? ORDER BY name LIMIT 100",
        (f"%{name}%",),
    )
    corps = [
        Corporation(
            company_id=r["company_id"], name=r["name"], jurisdiction=r["jurisdiction"],
            company_type=r["company_type"], incorporation_date=r["incorporation_date"],
            registered_address=r["registered_address"], status=r["status"],
            parent_company_id=r["parent_company_id"],
            officers=json.loads(r["officers"] or "[]"), source=r["source"],
        )
        for r in rows
    ]
    return CorpResult(query=name, corporations=corps, total=len(corps))
