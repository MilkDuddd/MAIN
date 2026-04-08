"""Billionaire wealth tracking via Wikidata and Forbes scraping."""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

from core import database, http_client
from core.config import WIKIDATA_SPARQL
from models.power import Billionaire, BillionairesResult

# Wikidata SPARQL query for billionaires
_SPARQL_QUERY = """
SELECT DISTINCT ?person ?personLabel ?countryLabel ?netWorth ?companyLabel ?dob WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P2218 ?netWorth.
  FILTER(?netWorth > 1000000000)
  OPTIONAL { ?person wdt:P27 ?country. }
  OPTIONAL { ?person wdt:P108 ?company. }
  OPTIONAL { ?person wdt:P569 ?dob. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY DESC(?netWorth)
LIMIT 200
"""


def fetch_wikidata_billionaires() -> list[Billionaire]:
    """Fetch billionaires from Wikidata SPARQL (net worth field)."""
    try:
        resp = http_client.get(
            WIKIDATA_SPARQL,
            params={"query": _SPARQL_QUERY, "format": "json"},
            headers={"Accept": "application/sparql-results+json"},
            source="Wikidata",
            timeout=60,
        )
        rows = resp.json().get("results", {}).get("bindings", [])
        billionaires: list[Billionaire] = []
        seen: set[str] = set()
        for i, row in enumerate(rows):
            name = row.get("personLabel", {}).get("value", "")
            if not name or name.startswith("Q") or name in seen:
                continue
            seen.add(name)
            wid = row.get("person", {}).get("value", "").split("/")[-1]
            net_worth_raw = row.get("netWorth", {}).get("value")
            try:
                net_worth = float(net_worth_raw) if net_worth_raw else None
            except ValueError:
                net_worth = None
            billionaires.append(Billionaire(
                name=name,
                source_rank=i + 1,
                net_worth_usd=net_worth,
                source="Wikidata",
                country=row.get("countryLabel", {}).get("value"),
                primary_company=row.get("companyLabel", {}).get("value"),
                wikidata_id=wid,
            ))
        return billionaires
    except Exception:
        return []


def fetch_forbes_public() -> list[Billionaire]:
    """
    Scrape Forbes Real-Time Billionaires list (public page).
    Falls back gracefully if structure changes.
    """
    try:
        resp = http_client.get(
            "https://www.forbes.com/real-time-billionaires/",
            source="Forbes",
            timeout=30,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        # Forbes embeds list data in a script tag as JSON
        for script in soup.find_all("script"):
            text = script.string or ""
            if "finalWorth" in text and "personName" in text:
                # Extract JSON array
                m = re.search(r"var FAPI_PARTICIPANTS = (\[.*?\]);", text, re.DOTALL)
                if not m:
                    m = re.search(r'"personsList":\s*(\[.*?\])', text, re.DOTALL)
                if m:
                    try:
                        persons = json.loads(m.group(1))
                        return [
                            Billionaire(
                                name=p.get("personName", ""),
                                source_rank=p.get("rank"),
                                net_worth_usd=p.get("finalWorth", 0) * 1e6,  # Forbes lists in $M
                                source="Forbes",
                                country=p.get("country"),
                                industry=p.get("industries", [None])[0] if p.get("industries") else None,
                                age=p.get("age"),
                                primary_company=p.get("organization"),
                            )
                            for p in persons if p.get("personName")
                        ]
                    except (json.JSONDecodeError, KeyError):
                        pass
        return []
    except Exception:
        return []


def update_billionaires() -> None:
    """Scheduled job: refresh billionaire list."""
    billionaires = fetch_wikidata_billionaires()
    if not billionaires:
        billionaires = fetch_forbes_public()
    _save(billionaires)


def _save(billionaires: list[Billionaire]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            b.source_rank, b.name, b.net_worth_usd, b.source, b.country,
            b.industry, b.age, b.primary_company, b.wikidata_id, now,
        )
        for b in billionaires
    ]
    if rows:
        # Clear old data and re-insert for fresh snapshot
        database.execute_write("DELETE FROM billionaires WHERE source=?", ("Wikidata",))
        database.execute_many(
            """INSERT INTO billionaires
            (source_rank, name, net_worth_usd, source, country, industry, age, primary_company, wikidata_id, collected_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )


def search_db(country: Optional[str] = None, top_n: int = 100) -> BillionairesResult:
    """Query cached billionaires from the database."""
    if country:
        rows = database.execute(
            "SELECT * FROM billionaires WHERE country LIKE ? ORDER BY source_rank ASC LIMIT ?",
            (f"%{country}%", top_n),
        )
    else:
        rows = database.execute(
            "SELECT * FROM billionaires ORDER BY source_rank ASC LIMIT ?",
            (top_n,),
        )
    billionaires = [
        Billionaire(
            name=r["name"], source_rank=r["source_rank"], net_worth_usd=r["net_worth_usd"],
            source=r["source"], country=r["country"], industry=r["industry"],
            age=r["age"], primary_company=r["primary_company"], wikidata_id=r["wikidata_id"],
        )
        for r in rows
    ]
    return BillionairesResult(country_filter=country, top_n=top_n, billionaires=billionaires, total=len(billionaires))
