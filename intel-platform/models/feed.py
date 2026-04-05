"""Live feed data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FeedItem:
    feed_id: str
    source: str
    title: str
    url: Optional[str] = None
    published_at: Optional[str] = None
    summary: Optional[str] = None
    full_text: Optional[str] = None
    category: Optional[str] = None   # geopolitical, uap, power, osint, general
    matched_keywords: list[str] = field(default_factory=list)
    collected_at: Optional[str] = None


@dataclass
class Alert:
    alert_id: str
    keyword: Optional[str] = None
    entity_name: Optional[str] = None
    triggered_by: Optional[str] = None
    message: str = ""
    severity: str = "info"    # info, warning, critical
    acknowledged: bool = False
    created_at: Optional[str] = None


@dataclass
class FeedStats:
    total_items: int = 0
    items_by_category: dict = field(default_factory=dict)
    items_by_source: dict = field(default_factory=dict)
    active_alerts: int = 0
    last_updated: Optional[str] = None
