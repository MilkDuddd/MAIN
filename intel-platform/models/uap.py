"""UAP / Anomalous phenomena data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UAPSighting:
    report_id: Optional[str] = None
    source: str = "NUFORC"
    occurred_date: Optional[str] = None
    reported_date: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    shape: Optional[str] = None
    duration_sec: Optional[int] = None
    description: Optional[str] = None
    posted_url: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


@dataclass
class SightingsResult:
    state_filter: Optional[str] = None
    days_filter: Optional[int] = None
    sightings: list[UAPSighting] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class UAPReport:
    report_id: str
    source: str  # Congressional, DIA, Navy, AARO, BlackVault
    title: str
    report_date: Optional[str] = None
    classification: Optional[str] = None
    summary: Optional[str] = None
    full_text: Optional[str] = None
    document_url: Optional[str] = None


@dataclass
class HearingTranscript:
    hearing_id: str
    title: str
    date: Optional[str] = None
    committee: Optional[str] = None
    chamber: Optional[str] = None  # Senate, House
    witnesses: list[str] = field(default_factory=list)
    summary: Optional[str] = None
    key_quotes: list[str] = field(default_factory=list)
    document_url: Optional[str] = None


@dataclass
class HearingsResult:
    keyword_filter: Optional[str] = None
    hearings: list[HearingTranscript] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class UAPNewsItem:
    title: str
    source: str
    published_at: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    matched_keywords: list[str] = field(default_factory=list)


@dataclass
class UAPNewsResult:
    days_filter: int = 7
    items: list[UAPNewsItem] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None
