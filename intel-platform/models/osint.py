"""OSINT data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WhoisResult:
    domain: str
    registrar: Optional[str] = None
    registrant_name: Optional[str] = None
    registrant_org: Optional[str] = None
    registrant_email: Optional[str] = None
    registrant_country: Optional[str] = None
    created_date: Optional[str] = None
    expiry_date: Optional[str] = None
    updated_date: Optional[str] = None
    name_servers: list[str] = field(default_factory=list)
    raw_text: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DnsRecord:
    domain: str
    record_type: str   # A, AAAA, MX, TXT, NS, CNAME, SOA
    value: str
    ttl: Optional[int] = None


@dataclass
class DnsResult:
    domain: str
    records: list[DnsRecord] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class CertEntry:
    domain: str
    cert_id: Optional[str] = None
    issuer: Optional[str] = None
    common_name: Optional[str] = None
    san_names: list[str] = field(default_factory=list)
    not_before: Optional[str] = None
    not_after: Optional[str] = None


@dataclass
class CertResult:
    domain: str
    entries: list[CertEntry] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class SocialPresence:
    username: str
    platform: str
    profile_url: Optional[str] = None
    exists: bool = False
    status_code: Optional[int] = None


@dataclass
class SocialResult:
    username: str
    platforms: list[SocialPresence] = field(default_factory=list)


@dataclass
class GitHubProfile:
    username: str
    name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    email: Optional[str] = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    created_at: Optional[str] = None
    repos: list[dict] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ShodanHost:
    ip: str
    hostnames: list[str] = field(default_factory=list)
    org: Optional[str] = None
    country: Optional[str] = None
    open_ports: list[int] = field(default_factory=list)
    vulns: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    last_update: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DorkResult:
    query: str
    engine: str
    results: list[dict] = field(default_factory=list)
    error: Optional[str] = None
