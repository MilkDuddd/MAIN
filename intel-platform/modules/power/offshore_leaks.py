"""ICIJ Offshore Leaks — Panama Papers, Pandora Papers, Offshore Leaks, Paradise Papers."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database
from core.http_client import get

_BASE = "https://offshoreleaks.icij.org/api/search"


def search(query: str, limit: int = 50) -> list[dict]:
    """Search ICIJ Offshore Leaks database."""
    params = {"q": query, "cat": "1", "utf8": "✓"}
    results = []
    try:
        resp = get(_BASE, params=params)
        data = resp.json() if resp.status_code == 200 else {}
        nodes = data.get("nodes", []) if isinstance(data, dict) else []
        for node in nodes[:limit]:
            results.append({
                "icij_node_id": str(node.get("node_id", "")),
                "name": node.get("name", ""),
                "entity_type": node.get("node_type", ""),
                "jurisdiction": node.get("jurisdiction", ""),
                "country_codes": json.dumps(node.get("country_codes", [])),
                "data_source": node.get("sourceID", ""),
                "valid_until": node.get("valid_until", ""),
            })
    except Exception:
        pass
    return results


def search_and_store(query: str, limit: int = 50) -> list[dict]:
    """Search ICIJ, store results in DB, return matches."""
    results = search(query, limit)
    if not results:
        return results
    now = datetime.now(timezone.utc).isoformat()
    for r in results:
        database.execute_write(
            """INSERT OR REPLACE INTO offshore_entities
               (icij_node_id, name, entity_type, jurisdiction, country_codes, data_source, valid_until, collected_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (r["icij_node_id"], r["name"], r["entity_type"], r["jurisdiction"],
             r["country_codes"], r["data_source"], r["valid_until"], now),
        )
    return results


def search_db(query: str) -> list[dict]:
    """Fuzzy search stored offshore entities."""
    rows = database.execute(
        "SELECT * FROM offshore_entities WHERE name LIKE ? ORDER BY name LIMIT 100",
        (f"%{query}%",),
    )
    return [dict(r) for r in rows]
