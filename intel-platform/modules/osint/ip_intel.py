"""IP Intelligence — ip-api.com (free, no key, geo + ISP + threat flags)."""
from datetime import datetime, timezone

from core import database
from core.config import IPAPI_URL
from core.http_client import get

_FIELDS = "status,message,country,countryCode,regionName,city,isp,org,as,reverse,mobile,proxy,hosting,query"


def lookup_ip(ip: str) -> dict:
    """Full IP lookup via ip-api.com — geo, ISP, proxy/hosting detection."""
    result = {}
    try:
        resp = get(f"{IPAPI_URL}/{ip}", params={"fields": _FIELDS}, timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json()
        if data.get("status") == "fail":
            return {"error": data.get("message", "Lookup failed")}
        result = {
            "ip_address":  data.get("query", ip),
            "hostname":    data.get("reverse", ""),
            "city":        data.get("city", ""),
            "region":      data.get("regionName", ""),
            "country":     data.get("country", ""),
            "country_code": data.get("countryCode", ""),
            "org":         data.get("org", ""),
            "isp":         data.get("isp", ""),
            "asn":         data.get("as", ""),
            "is_mobile":   1 if data.get("mobile") else 0,
            "is_proxy":    1 if data.get("proxy") else 0,
            "is_hosting":  1 if data.get("hosting") else 0,
            "is_vpn":      0,
            "is_tor":      0,
            "loc":         "",
            "postal":      "",
            "timezone":    "",
            "abuse_score": 0,
            "abuse_reports": 0,
        }
        _store(result)
    except Exception as e:
        result = {"error": str(e)}
    return result


# Keep lookup_full as an alias so existing callers don't break
def lookup_full(ip: str) -> dict:
    result = lookup_ip(ip)
    return {"ipinfo": result, "abuse": {}}


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
