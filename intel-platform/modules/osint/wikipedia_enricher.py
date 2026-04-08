"""Wikipedia / MediaWiki API — entity enrichment with summaries and key facts."""
from datetime import datetime, timezone
from typing import Optional

from core import database
from core.config import WIKIPEDIA_API
from core.http_client import get


def get_summary(entity_name: str) -> dict:
    """Fetch Wikipedia summary and key facts for an entity."""
    params = {
        "action": "query",
        "format": "json",
        "titles": entity_name,
        "prop": "extracts|info|categories|pageimages",
        "exintro": True,
        "explaintext": True,
        "inprop": "url",
        "piprop": "original",
        "redirects": 1,
    }
    result = {}
    try:
        resp = get(WIKIPEDIA_API, params=params, timeout=15)
        if resp.status_code != 200:
            return result
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            if page_id == "-1":
                continue
            result = {
                "title": page.get("title", ""),
                "summary": page.get("extract", "")[:2000],
                "url": page.get("fullurl", ""),
                "last_revised": page.get("touched", ""),
                "categories": [c["title"] for c in page.get("categories", [])[:10]],
                "image_url": page.get("original", {}).get("source", ""),
            }
            break
    except Exception:
        pass
    return result


def search_opensearch(query: str, limit: int = 10) -> list[str]:
    """Search Wikipedia for matching page titles."""
    params = {
        "action": "opensearch",
        "format": "json",
        "search": query,
        "limit": limit,
        "namespace": 0,
    }
    try:
        resp = get(WIKIPEDIA_API, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data[1] if len(data) > 1 else []
    except Exception:
        pass
    return []


def enrich_entity(entity_name: str) -> dict:
    """Get Wikipedia info for an entity and update its DB record if present."""
    info = get_summary(entity_name)
    if info and info.get("summary"):
        # Try to attach notes to the entity record
        rows = database.execute(
            "SELECT entity_id FROM entities WHERE canonical_name LIKE ? LIMIT 1",
            (f"%{entity_name}%",),
        )
        if rows:
            eid = rows[0]["entity_id"]
            database.execute_write(
                "UPDATE entities SET notes=?, updated_at=? WHERE entity_id=?",
                (info["summary"][:1000], datetime.now(timezone.utc).isoformat(), eid),
            )
    return info
