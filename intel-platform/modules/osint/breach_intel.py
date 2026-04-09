"""Have I Been Pwned — domain breach lookups (free, no key required).

Note: Email-level breach lookups require an HIBP subscription ($3.50/mo).
This module only supports domain-level checks which are free and keyless.
"""
import json
from datetime import datetime, timezone

from core import database
from core.config import HIBP_API
from core.http_client import get

_HEADERS = {"user-agent": "IntelPlatform/2.1"}


def check_domain(domain: str) -> list[dict]:
    """Check if a domain appears in any known data breaches (free, no key)."""
    breaches = []
    try:
        resp = get(f"{HIBP_API}/breaches", headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return breaches
        domain_clean = domain.lower().strip()
        for b in resp.json():
            if domain_clean in (b.get("Domain") or "").lower():
                breaches.append({
                    "target":       domain,
                    "breach_name":  b.get("Name", ""),
                    "breach_date":  b.get("BreachDate", ""),
                    "pwn_count":    b.get("PwnCount", 0),
                    "data_classes": json.dumps(b.get("DataClasses", [])),
                    "description":  (b.get("Description") or "")[:300],
                    "is_verified":  1 if b.get("IsVerified") else 0,
                    "is_sensitive": 1 if b.get("IsSensitive") else 0,
                    "source":       "HIBP",
                })
    except Exception:
        pass
    return breaches


def check_and_store(target: str) -> list[dict]:
    """Check target and store results. Domain lookups are free; email lookups are not supported."""
    if "@" in target:
        return [{"error": "Email breach lookups require an HIBP subscription. "
                          "Domain lookups are free — try the domain name instead."}]
    results = check_domain(target)
    now = datetime.now(timezone.utc).isoformat()
    for r in results:
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
