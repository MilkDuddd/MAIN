"""WHOIS lookups and DNS enumeration."""

import socket
from datetime import datetime, timezone
from typing import Optional

import dns.resolver
import whois

from core import database
from models.osint import WhoisResult, DnsRecord, DnsResult

_RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA"]


def fetch_whois(domain: str) -> WhoisResult:
    """Perform WHOIS lookup for a domain."""
    try:
        w = whois.whois(domain)
        ns = w.name_servers
        if isinstance(ns, str):
            ns = [ns]
        ns = [str(s).lower() for s in (ns or [])]

        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        expiry = w.expiration_date
        if isinstance(expiry, list):
            expiry = expiry[0]
        updated = w.updated_date
        if isinstance(updated, list):
            updated = updated[0]

        result = WhoisResult(
            domain=domain,
            registrar=str(w.registrar or ""),
            registrant_name=str(w.name or ""),
            registrant_org=str(w.org or ""),
            registrant_email=str(w.emails[0] if isinstance(w.emails, list) else (w.emails or "")),
            registrant_country=str(w.country or ""),
            created_date=str(creation) if creation else None,
            expiry_date=str(expiry) if expiry else None,
            updated_date=str(updated) if updated else None,
            name_servers=ns,
            raw_text=w.text,
        )
        _save_whois(result)
        return result
    except Exception as e:
        return WhoisResult(domain=domain, error=str(e))


def _save_whois(r: WhoisResult) -> None:
    import json
    now = datetime.now(timezone.utc).isoformat()
    database.execute_write(
        """INSERT INTO whois_records
        (domain, registrar, registrant_name, registrant_org, registrant_email,
         registrant_country, created_date, expiry_date, updated_date, name_servers, raw_text, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            r.domain, r.registrar, r.registrant_name, r.registrant_org, r.registrant_email,
            r.registrant_country, r.created_date, r.expiry_date, r.updated_date,
            json.dumps(r.name_servers), r.raw_text, now,
        ),
    )


def fetch_dns(domain: str, record_types: Optional[list[str]] = None) -> DnsResult:
    """Enumerate DNS records for a domain."""
    types = record_types or _RECORD_TYPES
    records: list[DnsRecord] = []
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 10

    for rtype in types:
        try:
            answers = resolver.resolve(domain, rtype)
            for rdata in answers:
                records.append(DnsRecord(
                    domain=domain,
                    record_type=rtype,
                    value=str(rdata),
                    ttl=answers.rrset.ttl if answers.rrset else None,
                ))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
            continue
        except Exception:
            continue

    _save_dns(records)
    return DnsResult(domain=domain, records=records)


def _save_dns(records: list[DnsRecord]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [(r.domain, r.record_type, r.value, r.ttl, now) for r in records]
    database.execute_many(
        "INSERT INTO dns_records (domain, record_type, value, ttl, collected_at) VALUES (?,?,?,?,?)",
        rows,
    )
