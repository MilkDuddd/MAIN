"""Correlation engine data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Entity:
    entity_id: str
    canonical_name: str
    entity_type: str   # person, organization, location, vessel, aircraft
    aliases: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source_modules: list[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Relationship:
    source_id: str
    target_id: str
    rel_type: str
    confidence: float = 0.5
    source_module: Optional[str] = None
    evidence: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class TimelineEvent:
    date: str
    event_type: str
    description: str
    source: str
    entity_id: Optional[str] = None
    url: Optional[str] = None


@dataclass
class EntityProfile:
    """Aggregated cross-source entity profile."""
    entity: Entity
    relationships: list[Relationship] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)

    # Per-module findings
    sanctions: list = field(default_factory=list)        # Sanction objects
    donations: list = field(default_factory=list)        # Donation objects
    board_roles: list = field(default_factory=list)      # BoardMember objects
    corporations: list = field(default_factory=list)     # Corporation objects
    flights: list = field(default_factory=list)          # FlightTrack objects (if aircraft)
    vessels: list = field(default_factory=list)          # VesselTrack objects (if vessel)
    uap_mentions: list = field(default_factory=list)     # UAPReport/HearingTranscript
    news_items: list = field(default_factory=list)       # FeedItem objects

    ai_summary: Optional[str] = None
    error: Optional[str] = None


@dataclass
class GraphData:
    nodes: list[dict] = field(default_factory=list)   # {id, label, type}
    edges: list[dict] = field(default_factory=list)   # {source, target, type, weight}
