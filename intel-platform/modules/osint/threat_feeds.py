"""AlienVault OTX — Open Threat Exchange, IOC lookup, APT group intelligence."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database, settings
from core.config import OTX_API
from core.http_client import get


def _headers() -> dict:
    key = settings.get("otx_key", "")
    return {"X-OTX-API-KEY": key} if key else {}


def lookup_ioc(indicator: str, indicator_type: Optional[str] = None) -> dict:
    """
    Look up an indicator of compromise.
    indicator_type: domain, IPv4, IPv6, URL, FileHash-SHA256, CVE
    """
    if not indicator_type:
        indicator_type = _guess_type(indicator)

    headers = _headers()
    if not headers:
        return {"error": "No OTX API key. Run: intel settings set otx_key YOUR_KEY"}

    endpoint = f"{OTX_API}/indicators/{indicator_type}/{indicator}/general"
    result = {}
    try:
        resp = get(endpoint, headers=headers, timeout=20)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json()
        pulse_info = data.get("pulse_info", {})
        result = {
            "indicator": indicator,
            "indicator_type": indicator_type,
            "source": "AlienVault OTX",
            "malicious_votes": pulse_info.get("count", 0),
            "suspicious_votes": 0,
            "clean_votes": 0,
            "categories": json.dumps([p.get("name", "") for p in pulse_info.get("pulses", [])[:5]]),
            "last_analysis": data.get("whois", "")[:50] if indicator_type == "domain" else "",
            "reputation_score": data.get("reputation", 0),
            "raw_data": json.dumps({
                "asn": data.get("asn", ""),
                "country_name": data.get("country_name", ""),
                "city": data.get("city", ""),
                "pulse_count": pulse_info.get("count", 0),
                "tags": data.get("tags", []),
            }),
        }
        _store(result)
    except Exception as e:
        result = {"error": str(e)}
    return result


def get_subscribed_pulses(limit: int = 20) -> list[dict]:
    """Fetch latest threat pulses from subscribed OTX feeds."""
    headers = _headers()
    if not headers:
        return []
    pulses = []
    try:
        resp = get(f"{OTX_API}/pulses/subscribed", params={"limit": limit},
                   headers=headers, timeout=20)
        if resp.status_code == 200:
            for p in resp.json().get("results", []):
                pulses.append({
                    "name": p.get("name", ""),
                    "description": p.get("description", "")[:200],
                    "tags": p.get("tags", []),
                    "indicators_count": p.get("indicators_count", 0),
                    "created": p.get("created", ""),
                    "author": p.get("author_name", ""),
                })
    except Exception:
        pass
    return pulses


def _guess_type(indicator: str) -> str:
    import re
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", indicator):
        return "IPv4"
    if re.match(r"^[0-9a-fA-F]{64}$", indicator):
        return "FileHash-SHA256"
    if re.match(r"^CVE-\d{4}-\d+$", indicator, re.IGNORECASE):
        return "CVE"
    if indicator.startswith("http"):
        return "URL"
    return "domain"


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
        "SELECT * FROM threat_intel WHERE source='AlienVault OTX' AND indicator LIKE ? ORDER BY collected_at DESC LIMIT 50",
        (f"%{indicator}%",),
    )
    return [dict(r) for r in rows]
