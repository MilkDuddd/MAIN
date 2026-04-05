"""IP Intelligence — IPinfo geolocation/ASN + AbuseIPDB reputation."""
import json
from datetime import datetime, timezone

from core import database, settings
from core.config import IPINFO_API, ABUSEIPDB_API
from core.http_client import get


def lookup_ipinfo(ip: str) -> dict:
    """Fetch geolocation and ASN data from IPinfo."""
    key = settings.get("ipinfo_key", "")
    params = {"token": key} if key else {}
    result = {}
    try:
        resp = get(f"{IPINFO_API}/{ip}/json", params=params, timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json()
        # Parse privacy flags if present
        privacy = data.get("privacy", {})
        asn_info = data.get("asn", {})
        result = {
            "ip_address": ip,
            "hostname": data.get("hostname", ""),
            "city": data.get("city", ""),
            "region": data.get("region", ""),
            "country": data.get("country", ""),
            "loc": data.get("loc", ""),
            "org": data.get("org", asn_info.get("name", "")),
            "asn": asn_info.get("asn", data.get("org", "").split()[0] if data.get("org", "").startswith("AS") else ""),
            "postal": data.get("postal", ""),
            "timezone": data.get("timezone", ""),
            "is_vpn": 1 if privacy.get("vpn") else 0,
            "is_proxy": 1 if privacy.get("proxy") else 0,
            "is_tor": 1 if privacy.get("tor") else 0,
            "is_hosting": 1 if privacy.get("hosting") else 0,
        }
    except Exception as e:
        result = {"error": str(e)}
    return result


def lookup_abuseipdb(ip: str) -> dict:
    """Check IP abuse history via AbuseIPDB."""
    key = settings.get("abuseipdb_key", "")
    if not key:
        return {"error": "No AbuseIPDB key. Run: intel settings set abuseipdb_key YOUR_KEY"}
    headers = {"Key": key, "Accept": "application/json"}
    result = {}
    try:
        resp = get(f"{ABUSEIPDB_API}/check", params={"ipAddress": ip, "maxAgeInDays": 90},
                   headers=headers, timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json().get("data", {})
        result = {
            "abuse_score": data.get("abuseConfidenceScore", 0),
            "abuse_reports": data.get("totalReports", 0),
            "country": data.get("countryCode", ""),
            "isp": data.get("isp", ""),
            "domain": data.get("domain", ""),
            "is_tor": 1 if data.get("isTor") else 0,
            "last_reported": data.get("lastReportedAt", ""),
        }
    except Exception as e:
        result = {"error": str(e)}
    return result


def lookup_full(ip: str) -> dict:
    """Full IP lookup: IPinfo + AbuseIPDB combined."""
    info = lookup_ipinfo(ip)
    abuse = lookup_abuseipdb(ip)
    if "error" not in info:
        info["abuse_score"] = abuse.get("abuse_score", 0)
        info["abuse_reports"] = abuse.get("abuse_reports", 0)
        _store(info)
    return {"ipinfo": info, "abuse": abuse}


def _store(r: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    database.execute_write(
        """INSERT INTO ip_enrichment
           (ip_address, hostname, city, region, country, loc, org, asn, postal,
            timezone, is_vpn, is_proxy, is_tor, is_hosting, abuse_score, abuse_reports, collected_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (r.get("ip_address", ""), r.get("hostname", ""), r.get("city", ""),
         r.get("region", ""), r.get("country", ""), r.get("loc", ""),
         r.get("org", ""), r.get("asn", ""), r.get("postal", ""),
         r.get("timezone", ""), r.get("is_vpn", 0), r.get("is_proxy", 0),
         r.get("is_tor", 0), r.get("is_hosting", 0),
         r.get("abuse_score", 0), r.get("abuse_reports", 0), now),
    )


def search_db(ip: str) -> list[dict]:
    rows = database.execute(
        "SELECT * FROM ip_enrichment WHERE ip_address LIKE ? ORDER BY collected_at DESC LIMIT 20",
        (f"%{ip}%",),
    )
    return [dict(r) for r in rows]
