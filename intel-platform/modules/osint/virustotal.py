"""VirusTotal — domain/IP/hash/URL reputation and malware intelligence."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database, settings
from core.config import VIRUSTOTAL_API
from core.http_client import get


def _headers() -> dict:
    key = settings.get("virustotal_key", "")
    return {"x-apikey": key} if key else {}


def lookup_domain(domain: str) -> dict:
    """Check domain reputation."""
    return _lookup(domain, "domain", f"{VIRUSTOTAL_API}/domains/{domain}")


def lookup_ip(ip: str) -> dict:
    """Check IP reputation."""
    return _lookup(ip, "ip", f"{VIRUSTOTAL_API}/ip_addresses/{ip}")


def lookup_hash(sha256: str) -> dict:
    """Check file hash reputation."""
    return _lookup(sha256, "hash", f"{VIRUSTOTAL_API}/files/{sha256}")


def lookup_url(url: str) -> dict:
    """Check URL reputation (requires encoding)."""
    import base64
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    return _lookup(url, "url", f"{VIRUSTOTAL_API}/urls/{url_id}")


def _lookup(indicator: str, indicator_type: str, endpoint: str) -> dict:
    headers = _headers()
    if not headers:
        return {"error": "No VirusTotal API key configured. Run: intel settings set virustotal_key YOUR_KEY"}
    result = {}
    try:
        resp = get(endpoint, headers=headers, timeout=20)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json().get("data", {}).get("attributes", {})
        stats = data.get("last_analysis_stats", {})
        categories = list((data.get("categories") or {}).values())[:10]
        result = {
            "indicator": indicator,
            "indicator_type": indicator_type,
            "source": "VirusTotal",
            "malicious_votes": stats.get("malicious", 0),
            "suspicious_votes": stats.get("suspicious", 0),
            "clean_votes": stats.get("undetected", 0),
            "categories": json.dumps(categories),
            "last_analysis": data.get("last_analysis_date", ""),
            "reputation_score": data.get("reputation", 0),
            "raw_data": json.dumps({k: v for k, v in data.items() if k != "last_analysis_results"}),
        }
        _store(result)
    except Exception as e:
        result = {"error": str(e)}
    return result


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
