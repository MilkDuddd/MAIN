"""Geopolitical intelligence data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Leader:
    wikidata_id: str
    name: str
    role: str
    country: str
    country_code: Optional[str] = None
    party: Optional[str] = None
    in_office_since: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    image_url: Optional[str] = None
    wikipedia_url: Optional[str] = None


@dataclass
class LeadersResult:
    country_filter: Optional[str] = None
    leaders: list[Leader] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class PoliticalEvent:
    event_id: str
    source: str
    event_date: Optional[str] = None
    actor1: Optional[str] = None
    actor1_country: Optional[str] = None
    actor2: Optional[str] = None
    actor2_country: Optional[str] = None
    event_description: Optional[str] = None
    action_type: Optional[str] = None
    goldstein_scale: Optional[float] = None
    source_url: Optional[str] = None


@dataclass
class EventsResult:
    query: str
    events: list[PoliticalEvent] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class Sanction:
    sanction_id: str
    list_source: str    # OFAC, EU, UN
    entity_type: Optional[str] = None
    name: str = ""
    aliases: list[str] = field(default_factory=list)
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = None
    reason: Optional[str] = None
    programs: list[str] = field(default_factory=list)
    effective_date: Optional[str] = None


@dataclass
class SanctionResult:
    query: str
    matches: list[Sanction] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class ConflictEvent:
    event_id: str
    source: str
    event_date: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_type: Optional[str] = None
    actor1: Optional[str] = None
    actor2: Optional[str] = None
    fatalities: Optional[int] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class ConflictResult:
    country_filter: Optional[str] = None
    events: list[ConflictEvent] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class Tender:
    tender_id: str
    source: str
    title: Optional[str] = None
    description: Optional[str] = None
    agency: Optional[str] = None
    country: Optional[str] = None
    published_date: Optional[str] = None
    deadline_date: Optional[str] = None
    estimated_value_usd: Optional[float] = None
    award_status: Optional[str] = None
    awardee: Optional[str] = None
    naics_code: Optional[str] = None
    url: Optional[str] = None


@dataclass
class TenderResult:
    query: str
    tenders: list[Tender] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None
