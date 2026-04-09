"""US Congress member data via Wikidata SPARQL — no API key required."""
from datetime import datetime, timezone
from typing import Optional

from core import database, http_client
from core.config import WIKIDATA_SPARQL

_SPARQL_QUERY = """
SELECT DISTINCT ?person ?personLabel ?partyLabel ?chamberLabel ?stateLabel ?start WHERE {
  VALUES ?pos { wd:Q13218630 wd:Q4964182 }
  ?person p:P39 ?stmt.
  ?stmt ps:P39 ?pos; pq:P580 ?start.
  FILTER NOT EXISTS { ?stmt pq:P582 ?end }
  OPTIONAL { ?person wdt:P102 ?party. }
  OPTIONAL { ?stmt pq:P768 ?district. }
  OPTIONAL { ?person wdt:P6 ?stateLink. }
  BIND(IF(?pos = wd:Q13218630, "Senate", "House") AS ?chamber)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 600
"""


def _sparql(query: str) -> list[dict]:
    resp = http_client.get(
        WIKIDATA_SPARQL,
        params={"query": query, "format": "json"},
        headers={"Accept": "application/sparql-results+json"},
        source="Wikidata",
        timeout=60,
    )
    return resp.json().get("results", {}).get("bindings", [])


def get_member(name: str) -> list[dict]:
    """Search for US Congress members by name via Wikidata SPARQL."""
    rows = _sparql(_SPARQL_QUERY)
    members = []
    for row in rows:
        full_name = row.get("personLabel", {}).get("value", "")
        if not full_name or name.lower() not in full_name.lower():
            continue
        person_id = row.get("person", {}).get("value", "").split("/")[-1]
        members.append({
            "member_id":       person_id,
            "full_name":       full_name,
            "party":           row.get("partyLabel", {}).get("value", ""),
            "state":           row.get("stateLabel", {}).get("value", ""),
            "chamber":         row.get("chamberLabel", {}).get("value", ""),
            "district":        "",
            "in_office":       1,
            "dw_nominate":     None,
            "twitter_account": "",
            "url":             row.get("person", {}).get("value", ""),
        })
    return members


def store_members(members: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for m in members:
        database.execute_write(
            """INSERT OR REPLACE INTO congress_members
               (member_id, full_name, party, state, chamber, district, in_office,
                dw_nominate, twitter_account, url, collected_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (m["member_id"], m["full_name"], m["party"], m["state"], m["chamber"],
             m.get("district"), m.get("in_office", 1), m.get("dw_nominate"),
             m.get("twitter_account", ""), m.get("url", ""), now),
        )


def search_and_store(name: str) -> list[dict]:
    members = get_member(name)
    if members:
        store_members(members)
    return members


def search_db(query: str) -> list[dict]:
    rows = database.execute(
        "SELECT * FROM congress_members WHERE full_name LIKE ? OR state LIKE ? ORDER BY full_name LIMIT 50",
        (f"%{query}%", f"%{query}%"),
    )
    return [dict(r) for r in rows]
