"""FBI Wanted + Interpol Red Notices — global law enforcement wanted persons."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database
from core.config import FBI_WANTED_API, INTERPOL_API
from core.http_client import get


def fetch_fbi_wanted(query: Optional[str] = None, limit: int = 100) -> list[dict]:
    """Fetch FBI wanted persons list."""
    params: dict = {"page": 1, "pageSize": min(limit, 50)}
    if query:
        params["title"] = query
    persons = []
    try:
        resp = get(FBI_WANTED_API, params=params, timeout=20)
        if resp.status_code != 200:
            return persons
        data = resp.json()
        for item in data.get("items", []):
            aliases_raw = item.get("aliases") or []
            persons.append({
                "list_source": "FBI",
                "notice_id": f"fbi_{item.get('uid', '')}",
                "full_name": item.get("title", ""),
                "aliases": json.dumps(aliases_raw),
                "nationality": (item.get("nationality") or [""])[0] if item.get("nationality") else "",
                "date_of_birth": (item.get("dates_of_birth_used") or [""])[0] if item.get("dates_of_birth_used") else "",
                "sex": item.get("sex", ""),
                "charges": item.get("description", "")[:500] if item.get("description") else "",
                "reward_text": item.get("reward_text", "") or "",
                "image_url": item.get("images", [{}])[0].get("thumb", "") if item.get("images") else "",
                "details_url": item.get("url", "") or "",
            })
    except Exception:
        pass
    return persons


def fetch_interpol_notices(query: Optional[str] = None, limit: int = 50) -> list[dict]:
    """Fetch Interpol Red Notices."""
    params: dict = {"resultPerPage": min(limit, 20), "page": 1}
    if query:
        params["name"] = query
    persons = []
    try:
        resp = get(INTERPOL_API, params=params, timeout=20)
        if resp.status_code != 200:
            return persons
        data = resp.json()
        for item in data.get("_embedded", {}).get("notices", []):
            persons.append({
                "list_source": "INTERPOL",
                "notice_id": f"interpol_{item.get('entity_id', '')}",
                "full_name": f"{item.get('forename','')} {item.get('name','')}".strip(),
                "aliases": json.dumps([]),
                "nationality": item.get("nationalities", [""])[0] if item.get("nationalities") else "",
                "date_of_birth": item.get("date_of_birth", ""),
                "sex": item.get("sex_id", ""),
                "charges": item.get("charge", ""),
                "reward_text": "",
                "image_url": item.get("_links", {}).get("thumbnail", {}).get("href", ""),
                "details_url": item.get("_links", {}).get("self", {}).get("href", ""),
            })
    except Exception:
        pass
    return persons


def update_wanted() -> dict:
    """Fetch and store all FBI + Interpol wanted persons."""
    now = datetime.now(timezone.utc).isoformat()
    fbi = fetch_fbi_wanted()
    interpol = fetch_interpol_notices()
    all_persons = fbi + interpol
    count = 0
    for p in all_persons:
        try:
            database.execute_write(
                """INSERT OR REPLACE INTO wanted_persons
                   (list_source, notice_id, full_name, aliases, nationality,
                    date_of_birth, sex, charges, reward_text, image_url, details_url, collected_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (p["list_source"], p["notice_id"], p["full_name"], p["aliases"],
                 p["nationality"], p["date_of_birth"], p["sex"], p["charges"],
                 p["reward_text"], p["image_url"], p["details_url"], now),
            )
            count += 1
        except Exception:
            pass
    return {"fbi": len(fbi), "interpol": len(interpol), "stored": count}


def search(name: str) -> list[dict]:
    """Search wanted persons DB."""
    rows = database.execute(
        "SELECT * FROM wanted_persons WHERE full_name LIKE ? OR aliases LIKE ? ORDER BY list_source LIMIT 100",
        (f"%{name}%", f"%{name}%"),
    )
    return [dict(r) for r in rows]


def search_live(name: str) -> list[dict]:
    """Search FBI + Interpol live APIs."""
    return fetch_fbi_wanted(query=name) + fetch_interpol_notices(query=name)
