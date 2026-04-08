"""Email intelligence — local pattern guesser + MX record verification (no API key required)."""
import re
from typing import Optional


def guess_email_patterns(domain: str, first: str, last: str) -> list[dict]:
    """Generate common corporate email patterns for a person at a domain."""
    f = first.lower().strip()
    l = last.lower().strip()
    f1 = f[0] if f else ""
    l1 = l[0] if l else ""

    patterns = []
    candidates = []
    if f and l:
        candidates = [
            (f"{f}.{l}@{domain}",        "{first}.{last}"),
            (f"{f}{l}@{domain}",         "{first}{last}"),
            (f"{f1}{l}@{domain}",        "{f}{last}"),
            (f"{f1}.{l}@{domain}",       "{f}.{last}"),
            (f"{f}_{l}@{domain}",        "{first}_{last}"),
            (f"{f}@{domain}",            "{first}"),
            (f"{l}@{domain}",            "{last}"),
            (f"{l}.{f}@{domain}",        "{last}.{first}"),
            (f"{l}{f1}@{domain}",        "{last}{f}"),
            (f"{f}{l1}@{domain}",        "{first}{l}"),
        ]
    elif f:
        candidates = [(f"{f}@{domain}", "{first}")]
    elif l:
        candidates = [(f"{l}@{domain}", "{last}")]

    for email, pattern in candidates:
        if verify_email_format(email):
            mx_ok = _check_mx(domain)
            patterns.append({
                "email": email,
                "pattern": pattern,
                "domain": domain,
                "format_valid": True,
                "mx_valid": mx_ok,
                "confidence": 80 if mx_ok else 40,
            })

    return patterns


def verify_email_format(email: str) -> bool:
    """Validate email address format with regex."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def _check_mx(domain: str) -> bool:
    """Check if domain has MX records (means it accepts email)."""
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(list(answers)) > 0
    except Exception:
        return False


def domain_search(domain: str, limit: int = 25) -> dict:
    """Generate email pattern guesses for a domain (replaces Hunter.io)."""
    mx_ok = _check_mx(domain)
    common_prefixes = ["info", "contact", "admin", "support", "hello", "press", "media",
                       "hr", "jobs", "careers", "legal", "security", "privacy"]
    emails = []
    for prefix in common_prefixes[:limit]:
        email = f"{prefix}@{domain}"
        emails.append({
            "email": email,
            "first_name": "",
            "last_name": "",
            "position": "Generic",
            "confidence": 50 if mx_ok else 20,
            "sources": 0,
        })
    return {
        "domain": domain,
        "organization": "",
        "pattern": "pattern-unknown",
        "emails_found": len(emails),
        "mx_valid": mx_ok,
        "note": "Generated via local pattern analysis — no external API used",
        "emails": emails,
    }


def email_finder(domain: str, first_name: str, last_name: str) -> dict:
    """Find most likely email for a person at a domain using pattern guessing."""
    patterns = guess_email_patterns(domain, first_name, last_name)
    if not patterns:
        return {"error": "Could not generate patterns", "domain": domain,
                "first_name": first_name, "last_name": last_name}
    best = max(patterns, key=lambda p: p["confidence"])
    return {
        "email": best["email"],
        "score": best["confidence"],
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "all_patterns": patterns,
    }


def verify_email(email: str) -> dict:
    """Verify email format and check domain MX records."""
    fmt_ok = verify_email_format(email)
    domain = email.split("@")[-1] if "@" in email else ""
    mx_ok = _check_mx(domain) if domain else False
    return {
        "email": email,
        "status": "valid" if fmt_ok else "invalid",
        "result": "possible" if (fmt_ok and mx_ok) else ("format_invalid" if not fmt_ok else "no_mx"),
        "score": 70 if (fmt_ok and mx_ok) else (30 if fmt_ok else 0),
        "regexp": fmt_ok,
        "mx_records": mx_ok,
        "note": "Local verification only — no SMTP check performed",
    }
