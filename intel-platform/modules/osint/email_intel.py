"""Hunter.io — email intelligence, domain email patterns, address verification."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database, settings
from core.config import HUNTER_API
from core.http_client import get


def _params_base() -> dict:
    return {"api_key": settings.get("hunter_key", "")}


def _has_key() -> bool:
    return bool(settings.get("hunter_key", ""))


def domain_search(domain: str, limit: int = 25) -> dict:
    """Find all email addresses for a domain."""
    if not _has_key():
        return {"error": "Hunter.io API key required. Run: intel settings set hunter_key YOUR_KEY"}
    params = {**_params_base(), "domain": domain, "limit": limit}
    try:
        resp = get(f"{HUNTER_API}/domain-search", params=params, timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json().get("data", {})
        return {
            "domain": domain,
            "organization": data.get("organization", ""),
            "pattern": data.get("pattern", ""),
            "emails_found": data.get("emails_count", 0),
            "emails": [
                {
                    "email": e.get("value", ""),
                    "first_name": e.get("first_name", ""),
                    "last_name": e.get("last_name", ""),
                    "position": e.get("position", ""),
                    "confidence": e.get("confidence", 0),
                    "sources": len(e.get("sources", [])),
                }
                for e in data.get("emails", [])
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def verify_email(email: str) -> dict:
    """Verify if an email address is valid and deliverable."""
    if not _has_key():
        return {"error": "Hunter.io API key required. Run: intel settings set hunter_key YOUR_KEY"}
    params = {**_params_base(), "email": email}
    try:
        resp = get(f"{HUNTER_API}/email-verifier", params=params, timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json().get("data", {})
        return {
            "email": email,
            "status": data.get("status", ""),       # valid, invalid, accept_all, unknown
            "result": data.get("result", ""),        # deliverable, risky, undeliverable
            "score": data.get("score", 0),
            "regexp": data.get("regexp", False),
            "gibberish": data.get("gibberish", False),
            "disposable": data.get("disposable", False),
            "webmail": data.get("webmail", False),
            "mx_records": data.get("mx_records", False),
            "smtp_server": data.get("smtp_server", False),
            "smtp_check": data.get("smtp_check", False),
        }
    except Exception as e:
        return {"error": str(e)}


def email_finder(domain: str, first_name: str, last_name: str) -> dict:
    """Find most likely email for a person at a domain."""
    if not _has_key():
        return {"error": "Hunter.io API key required. Run: intel settings set hunter_key YOUR_KEY"}
    params = {**_params_base(), "domain": domain, "first_name": first_name, "last_name": last_name}
    try:
        resp = get(f"{HUNTER_API}/email-finder", params=params, timeout=15)
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        data = resp.json().get("data", {})
        return {
            "email": data.get("email", ""),
            "score": data.get("score", 0),
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "position": data.get("position", ""),
        }
    except Exception as e:
        return {"error": str(e)}
