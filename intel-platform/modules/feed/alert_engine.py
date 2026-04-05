"""Alert engine — match incoming feed items against tracked keywords and entities."""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from core import database, settings
from models.feed import Alert, FeedItem


def check_item(item: FeedItem) -> list[Alert]:
    """Check a feed item against configured alert keywords and tracked entities."""
    keywords: list[str] = settings.get("alert_keywords", [])
    tracked_entities: list[str] = settings.get("tracked_entities", [])
    alerts: list[Alert] = []
    combined = f"{item.title} {item.summary or ''}".lower()

    for kw in keywords:
        if kw.lower() in combined:
            alert_id = hashlib.md5(f"kw-{kw}-{item.feed_id}".encode()).hexdigest()
            alerts.append(Alert(
                alert_id=alert_id,
                keyword=kw,
                triggered_by=item.feed_id,
                message=f"Keyword '{kw}' found in: {item.title}",
                severity="info",
                created_at=datetime.now(timezone.utc).isoformat(),
            ))

    for entity in tracked_entities:
        if entity.lower() in combined:
            alert_id = hashlib.md5(f"ent-{entity}-{item.feed_id}".encode()).hexdigest()
            alerts.append(Alert(
                alert_id=alert_id,
                entity_name=entity,
                triggered_by=item.feed_id,
                message=f"Tracked entity '{entity}' mentioned in: {item.title}",
                severity="warning",
                created_at=datetime.now(timezone.utc).isoformat(),
            ))

    _save_alerts(alerts)
    return alerts


def _save_alerts(alerts: list[Alert]) -> None:
    rows = [
        (
            a.alert_id, a.keyword, a.entity_name, a.triggered_by,
            a.message, a.severity, 0, a.created_at,
        )
        for a in alerts
    ]
    if rows:
        database.execute_many(
            """INSERT OR IGNORE INTO alerts
            (alert_id, keyword, entity_name, triggered_by, message, severity, acknowledged, created_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            rows,
        )


def get_active_alerts(limit: int = 50) -> list[Alert]:
    """Get unacknowledged alerts."""
    rows = database.execute(
        "SELECT * FROM alerts WHERE acknowledged=0 ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    return [
        Alert(
            alert_id=r["alert_id"], keyword=r["keyword"], entity_name=r["entity_name"],
            triggered_by=r["triggered_by"], message=r["message"],
            severity=r["severity"], acknowledged=bool(r["acknowledged"]),
            created_at=r["created_at"],
        )
        for r in rows
    ]


def acknowledge(alert_id: str) -> None:
    database.execute_write("UPDATE alerts SET acknowledged=1 WHERE alert_id=?", (alert_id,))


def add_keyword(keyword: str) -> None:
    """Add a keyword to the alert watchlist."""
    keywords = settings.get("alert_keywords", [])
    if keyword not in keywords:
        keywords.append(keyword)
        settings.set("alert_keywords", keywords)


def add_entity(entity_name: str) -> None:
    """Add an entity name to the tracked entities watchlist."""
    entities = settings.get("tracked_entities", [])
    if entity_name not in entities:
        entities.append(entity_name)
        settings.set("tracked_entities", entities)


def remove_keyword(keyword: str) -> None:
    keywords = settings.get("alert_keywords", [])
    settings.set("alert_keywords", [k for k in keywords if k != keyword])


def list_keywords() -> list[str]:
    return settings.get("alert_keywords", [])


def list_entities() -> list[str]:
    return settings.get("tracked_entities", [])
