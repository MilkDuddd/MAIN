"""Have I Been Pwned — data breach lookups for domains and emails."""
import json
from datetime import datetime, timezone

from core import database, settings
from core.config import HIBP_API
from core.http_client import get


def _headers() -> dict:
    key = settings.get("hibp_key", "")
    headers = {"hibp-api-key": key} if key else {}
    headers["user-agent"] = "IntelPlatform/2.0"
    return headers


def check_domain(domain: str) -> list[dict]:
    """Check if a domain appears in any known data breaches (no key required)."""
    # Domain-level breach check via breached sites list
    breaches = []
    try:
        resp = get(f"{HIBP_API}/breaches", headers={"user-agent": "IntelPlatform/2.0"}, timeout=15)
        if resp.status_code != 200:
            return breaches
        all_breaches = resp.json()
        domain_clean = domain.lower().strip()
        for b in all_breaches:
            if domain_clean in (b.get("Domain") or "").lower():
                breaches.append({
                    "target": domain,
                    "breach_name": b.get("Name", ""),
                    "breach_date": b.get("BreachDate", ""),
                    "pwn_count": b.get("PwnCount", 0),
                    "data_classes": json.dumps(b.get("DataClasses", [])),
                    "description": (b.get("Description") or "")[:300],
                    "is_verified": 1 if b.get("IsVerified") else 0,
                    "is_sensitive": 1 if b.get("IsSensitive") else 0,
                    "source": "HIBP",
                })
    except Exception:
        pass
    return breaches


def check_email(email: str) -> list[dict]:
    """Check if an email appears in breaches (requires HIBP API key)."""
    headers = _headers()
    if not headers.get("hibp-api-key"):
        return [{"error": "HIBP API key required for email lookups. Run: intel settings set hibp_key YOUR_KEY"}]
    breaches = []
    try:
        resp = get(f"{HIBP_API}/breachedaccount/{email}", params={"truncateResponse": "false"},
                   headers=headers, timeout=15)
        if resp.status_code == 404:
            return []  # No breaches found
        if resp.status_code != 200:
            return [{"error": f"HTTP {resp.status_code}"}]
        for b in resp.json():
            breaches.append({
                "target": email,
                "breach_name": b.get("Name", ""),
                "breach_date": b.get("BreachDate", ""),
                "pwn_count": b.get("PwnCount", 0),
                "data_classes": json.dumps(b.get("DataClasses", [])),
                "description": (b.get("Description") or "")[:300],
                "is_verified": 1 if b.get("IsVerified") else 0,
                "is_sensitive": 1 if b.get("IsSensitive") else 0,
                "source": "HIBP",
            })
    except Exception:
        pass
    return breaches


def check_and_store(target: str) -> list[dict]:
    """Check target (domain or email) and store results."""
    if "@" in target:
        results = check_email(target)
    else:
        results = check_domain(target)

    now = datetime.now(timezone.utc).isoformat()
    for r in results:
        if "error" in r:
            continue
        database.execute_write(
            """INSERT INTO breach_records
               (target, breach_name, breach_date, pwn_count, data_classes,
                description, is_verified, is_sensitive, source, collected_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (r["target"], r["breach_name"], r["breach_date"], r.get("pwn_count", 0),
             r["data_classes"], r["description"], r.get("is_verified", 0),
             r.get("is_sensitive", 0), r["source"], now),
        )
    return results


def search_db(target: str) -> list[dict]:
    rows = database.execute(
        "SELECT * FROM breach_records WHERE target LIKE ? ORDER BY breach_date DESC LIMIT 100",
        (f"%{target}%",),
    )
    return [dict(r) for r in rows]
