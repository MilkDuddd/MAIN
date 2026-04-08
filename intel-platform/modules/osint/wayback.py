"""Wayback Machine / Archive.org CDX API — historical domain snapshots."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database
from core.config import WAYBACK_CDX
from core.http_client import get


def get_snapshots(url: str, limit: int = 50, from_year: Optional[str] = None,
                  to_year: Optional[str] = None) -> list[dict]:
    """Fetch archive snapshots for a URL."""
    params = {
        "url": url,
        "output": "json",
        "limit": limit,
        "fl": "timestamp,statuscode,mimetype,digest,original",
        "collapse": "timestamp:8",
    }
    if from_year:
        params["from"] = from_year
    if to_year:
        params["to"] = to_year

    snapshots = []
    try:
        resp = get(WAYBACK_CDX, params=params, timeout=20)
        if resp.status_code != 200:
            return snapshots
        rows = resp.json()
        if not rows or len(rows) < 2:
            return snapshots
        # First row is header
        header = rows[0]
        for row in rows[1:]:
            rec = dict(zip(header, row))
            ts = rec.get("timestamp", "")
            snapshots.append({
                "url": url,
                "timestamp": ts,
                "status_code": rec.get("statuscode", ""),
                "mime_type": rec.get("mimetype", ""),
                "digest": rec.get("digest", ""),
                "snapshot_url": f"https://web.archive.org/web/{ts}/{url}" if ts else "",
            })
    except Exception:
        pass
    return snapshots


def fetch_and_store(url: str, limit: int = 50) -> list[dict]:
    """Fetch snapshots and store in DB."""
    snapshots = get_snapshots(url, limit=limit)
    if not snapshots:
        return snapshots
    now = datetime.now(timezone.utc).isoformat()
    for s in snapshots:
        database.execute_write(
            """INSERT INTO wayback_snapshots
               (url, timestamp, status_code, mime_type, digest, snapshot_url, collected_at)
               VALUES (?,?,?,?,?,?,?)""",
            (s["url"], s["timestamp"], s["status_code"], s["mime_type"],
             s["digest"], s["snapshot_url"], now),
        )
    return snapshots


def search_db(url: str) -> list[dict]:
    rows = database.execute(
        "SELECT * FROM wayback_snapshots WHERE url LIKE ? ORDER BY timestamp DESC LIMIT 100",
        (f"%{url}%",),
    )
    return [dict(r) for r in rows]
