"""World leaders database via Wikidata SPARQL."""

import json
from datetime import datetime, timezone
from typing import Optional

from core import database, http_client
from core.config import WIKIDATA_SPARQL
from models.geopolitical import Leader, LeadersResult

# Roles to query from Wikidata
_ROLE_QUERIES = {
    "head_of_state": """
SELECT DISTINCT ?person ?personLabel ?countryLabel ?countryCode ?roleLabel ?partyLabel ?inOfficeSince ?dob ?image ?article WHERE {
  ?role wdt:P31 wd:Q30461.
  ?country wdt:P31/wdt:P279* wd:Q6256.
  ?country wdt:P35 ?person.
  OPTIONAL { ?country wdt:P297 ?countryCode. }
  OPTIONAL { ?person wdt:P102 ?party. }
  OPTIONAL { ?person p:P39 ?stmt. ?stmt ps:P39 ?role. ?stmt pq:P580 ?inOfficeSince. }
  OPTIONAL { ?person wdt:P569 ?dob. }
  OPTIONAL { ?person wdt:P18 ?image. }
  OPTIONAL { ?article schema:about ?person; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 300
""",
    "head_of_government": """
SELECT DISTINCT ?person ?personLabel ?countryLabel ?countryCode ?roleLabel ?partyLabel ?inOfficeSince ?dob ?image ?article WHERE {
  ?country wdt:P31/wdt:P279* wd:Q6256.
  ?country wdt:P6 ?person.
  OPTIONAL { ?country wdt:P297 ?countryCode. }
  OPTIONAL { ?person wdt:P102 ?party. }
  OPTIONAL { ?person p:P39 ?stmt. ?stmt ps:P39 ?role. ?stmt pq:P580 ?inOfficeSince. }
  OPTIONAL { ?person wdt:P569 ?dob. }
  OPTIONAL { ?person wdt:P18 ?image. }
  OPTIONAL { ?article schema:about ?person; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 300
""",
}


def _sparql(query: str) -> list[dict]:
    resp = http_client.get(
        WIKIDATA_SPARQL,
        params={"query": query, "format": "json"},
        headers={"Accept": "application/sparql-results+json"},
        source="Wikidata",
        timeout=60,
    )
    data = resp.json()
    return data.get("results", {}).get("bindings", [])


def _parse_binding(row: dict, role_label: str) -> Optional[Leader]:
    try:
        person_id = row["person"]["value"].split("/")[-1]
        name = row.get("personLabel", {}).get("value", "")
        if not name or name.startswith("Q"):
            return None
        return Leader(
            wikidata_id=person_id,
            name=name,
            role=row.get("roleLabel", {}).get("value", role_label),
            country=row.get("countryLabel", {}).get("value", ""),
            country_code=row.get("countryCode", {}).get("value"),
            party=row.get("partyLabel", {}).get("value"),
            in_office_since=row.get("inOfficeSince", {}).get("value", "")[:10] or None,
            date_of_birth=row.get("dob", {}).get("value", "")[:10] or None,
            image_url=row.get("image", {}).get("value"),
            wikipedia_url=row.get("article", {}).get("value"),
        )
    except (KeyError, ValueError):
        return None


def fetch_leaders(country_filter: Optional[str] = None) -> LeadersResult:
    """Fetch world leaders from Wikidata SPARQL."""
    leaders: list[Leader] = []
    seen_ids: set[str] = set()

    for role_key, query in _ROLE_QUERIES.items():
        role_label = role_key.replace("_", " ").title()
        try:
            rows = _sparql(query)
            for row in rows:
                leader = _parse_binding(row, role_label)
                if leader and leader.wikidata_id not in seen_ids:
                    if country_filter:
                        cf = country_filter.upper()
                        if cf not in (leader.country.upper(), (leader.country_code or "").upper()):
                            continue
                    seen_ids.add(leader.wikidata_id)
                    leaders.append(leader)
        except Exception as e:
            return LeadersResult(country_filter=country_filter, error=str(e))

    leaders.sort(key=lambda l: l.country)
    return LeadersResult(
        country_filter=country_filter,
        leaders=leaders,
        total=len(leaders),
    )


def update_leaders() -> None:
    """Scheduled job: refresh world leaders in the database."""
    result = fetch_leaders()
    if result.error or not result.leaders:
        return

    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            l.wikidata_id, l.name, l.role, l.country, l.country_code,
            l.party, l.in_office_since, l.date_of_birth,
            l.image_url, l.wikipedia_url, now,
        )
        for l in result.leaders
    ]
    database.execute_many(
        """INSERT OR REPLACE INTO world_leaders
        (wikidata_id, name, role, country, country_code, party,
         in_office_since, date_of_birth, image_url, wikipedia_url, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(country_filter: Optional[str] = None) -> LeadersResult:
    """Query cached leaders from the database."""
    if country_filter:
        rows = database.execute(
            "SELECT * FROM world_leaders WHERE country_code=? OR country LIKE ? ORDER BY country",
            (country_filter.upper(), f"%{country_filter}%"),
        )
    else:
        rows = database.execute("SELECT * FROM world_leaders ORDER BY country")

    leaders = [
        Leader(
            wikidata_id=r["wikidata_id"] or "",
            name=r["name"],
            role=r["role"],
            country=r["country"],
            country_code=r["country_code"],
            party=r["party"],
            in_office_since=r["in_office_since"],
            date_of_birth=r["date_of_birth"],
            image_url=r["image_url"],
            wikipedia_url=r["wikipedia_url"],
        )
        for r in rows
    ]
    return LeadersResult(country_filter=country_filter, leaders=leaders, total=len(leaders))
