"""Shodan API integration for host intelligence."""

from core import http_client, settings
from core.config import SHODAN_API
from models.osint import ShodanHost


def fetch_host(ip: str) -> ShodanHost:
    """Fetch Shodan intelligence for a specific IP address."""
    key = settings.get("shodan_api_key", "")
    if not key:
        return ShodanHost(ip=ip, error="No shodan_api_key configured")
    try:
        resp = http_client.get(
            f"{SHODAN_API}/shodan/host/{ip}",
            params={"key": key},
            source="Shodan",
            timeout=30,
        )
        data = resp.json()
        if "error" in data:
            return ShodanHost(ip=ip, error=data["error"])
        return ShodanHost(
            ip=ip,
            hostnames=data.get("hostnames", []),
            org=data.get("org"),
            country=data.get("country_name"),
            open_ports=data.get("ports", []),
            vulns=list(data.get("vulns", {}).keys()),
            tags=data.get("tags", []),
            last_update=data.get("last_update"),
        )
    except Exception as e:
        return ShodanHost(ip=ip, error=str(e))


def search_shodan(query: str, limit: int = 10) -> list[ShodanHost]:
    """Perform a Shodan search and return host summaries."""
    key = settings.get("shodan_api_key", "")
    if not key:
        return [ShodanHost(ip="N/A", error="No shodan_api_key configured")]
    try:
        resp = http_client.get(
            f"{SHODAN_API}/shodan/host/search",
            params={"key": key, "query": query, "facets": "country,org", "page": 1},
            source="Shodan",
            timeout=30,
        )
        data = resp.json()
        matches = data.get("matches", [])[:limit]
        return [
            ShodanHost(
                ip=m.get("ip_str", ""),
                hostnames=m.get("hostnames", []),
                org=m.get("org"),
                country=m.get("location", {}).get("country_name"),
                open_ports=[m.get("port")] if m.get("port") else [],
                tags=m.get("tags", []),
                last_update=m.get("timestamp"),
            )
            for m in matches
        ]
    except Exception as e:
        return [ShodanHost(ip="N/A", error=str(e))]
