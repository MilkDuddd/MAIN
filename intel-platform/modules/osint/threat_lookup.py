"""Threat Intel — abuse.ch (URLhaus + MalwareBazaar) — free, no API key required."""
import json
import re
from datetime import datetime, timezone

from core import database
from core.config import URLHAUS_API, MALWAREBAZAAR_API
from core.http_client import post as http_post


def lookup_urlhaus(indicator: str) -> dict:
    """Query URLhaus for a host/domain/IP."""
    result = {}
    try:
        resp = http_post(URLHAUS_API, data={"host": indicator}, timeout=20)
        if resp.status_code != 200:
            return {"error": f"URLhaus HTTP {resp.status_code}"}
        data = resp.json()
        query_status = data.get("query_status", "")
        if query_status == "no_results":
            return {
                "indicator": indicator,
                "indicator_type": "host",
                "source": "URLhaus",
                "malicious_votes": 0,
                "suspicious_votes": 0,
                "clean_votes": 1,
                "categories": "[]",
                "last_analysis": "",
                "reputation_score": 0,
                "raw_data": json.dumps({"query_status": "no_results"}),
            }
        blacklists = data.get("blacklists", {})
        urls = data.get("urls", [])
        tags = list({tag for u in urls for tag in (u.get("tags") or [])})[:10]
        result = {
            "indicator": indicator,
            "indicator_type": "host",
            "source": "URLhaus",
            "malicious_votes": len(urls),
            "suspicious_votes": 0,
            "clean_votes": 0,
            "categories": json.dumps(tags),
            "last_analysis": data.get("date_added", ""),
            "reputation_score": -len(urls),
            "raw_data": json.dumps({
                "url_count": data.get("url_count", len(urls)),
                "blacklisted_surbl": blacklists.get("surbl", ""),
                "blacklisted_gsbe": blacklists.get("gsbe_toxicity", ""),
                "urls_sample": [u.get("url", "") for u in urls[:5]],
            }),
        }
        _store(result)
    except Exception as e:
        result = {"error": str(e)}
    return result


def lookup_malwarebazaar(sha256_hash: str) -> dict:
    """Query MalwareBazaar for a SHA256 hash."""
    result = {}
    try:
        resp = http_post(MALWAREBAZAAR_API,
                         data={"query": "get_info", "hash": sha256_hash}, timeout=20)
        if resp.status_code != 200:
            return {"error": f"MalwareBazaar HTTP {resp.status_code}"}
        data = resp.json()
        if data.get("query_status") != "ok":
            return {
                "indicator": sha256_hash,
                "indicator_type": "hash",
                "source": "MalwareBazaar",
                "malicious_votes": 0,
                "suspicious_votes": 0,
                "clean_votes": 1,
                "categories": "[]",
                "last_analysis": "",
                "reputation_score": 0,
                "raw_data": json.dumps({"query_status": data.get("query_status")}),
            }
        info = (data.get("data") or [{}])[0]
        tags = info.get("tags") or []
        result = {
            "indicator": sha256_hash,
            "indicator_type": "hash",
            "source": "MalwareBazaar",
            "malicious_votes": 1,
            "suspicious_votes": 0,
            "clean_votes": 0,
            "categories": json.dumps(tags[:10]),
            "last_analysis": info.get("first_seen", ""),
            "reputation_score": -100,
            "raw_data": json.dumps({
                "file_type": info.get("file_type", ""),
                "signature": info.get("signature", ""),
                "reporter": info.get("reporter", ""),
                "first_seen": info.get("first_seen", ""),
                "tags": tags[:10],
            }),
        }
        _store(result)
    except Exception as e:
        result = {"error": str(e)}
    return result


def lookup_indicator(indicator: str) -> dict:
    """Auto-detect indicator type and query appropriate abuse.ch API."""
    # SHA256 hash
    if re.match(r"^[0-9a-fA-F]{64}$", indicator):
        return lookup_malwarebazaar(indicator)
    # IP or domain/host
    return lookup_urlhaus(indicator)


def _store(r: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    database.execute_write(
        """INSERT INTO threat_intel
           (indicator, indicator_type, source, malicious_votes, suspicious_votes,
            clean_votes, categories, last_analysis, reputation_score, raw_data, collected_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (r["indicator"], r["indicator_type"], r["source"],
         r.get("malicious_votes", 0), r.get("suspicious_votes", 0),
         r.get("clean_votes", 0), r.get("categories", "[]"),
         r.get("last_analysis", ""), r.get("reputation_score", 0),
         r.get("raw_data", "{}"), now),
    )


def search_db(indicator: str) -> list[dict]:
    rows = database.execute(
        "SELECT * FROM threat_intel WHERE indicator LIKE ? ORDER BY collected_at DESC LIMIT 50",
        (f"%{indicator}%",),
    )
    return [dict(r) for r in rows]
