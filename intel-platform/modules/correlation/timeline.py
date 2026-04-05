"""Timeline construction — chronological event sequence for an entity."""

from datetime import datetime, timezone
from typing import Optional

from core import database
from models.correlation import TimelineEvent


def build_entity_timeline(name: str) -> list[TimelineEvent]:
    """Aggregate all dated events related to a named entity across all tables."""
    events: list[TimelineEvent] = []
    q = f"%{name}%"

    # Sanctions
    rows = database.execute(
        "SELECT name, effective_date, list_source FROM sanctions WHERE name LIKE ? AND effective_date IS NOT NULL",
        (q,),
    )
    for r in rows:
        events.append(TimelineEvent(
            date=r["effective_date"],
            event_type="Sanctioned",
            description=f"Added to {r['list_source']} sanctions list as: {r['name']}",
            source=r["list_source"],
        ))

    # Political donations
    rows = database.execute(
        """SELECT donor_name, recipient_name, amount_usd, transaction_date, recipient_party
           FROM political_donations WHERE (donor_name LIKE ? OR recipient_name LIKE ?)
           AND transaction_date IS NOT NULL""",
        (q, q),
    )
    for r in rows:
        amt = f"${r['amount_usd']:,.0f}" if r["amount_usd"] else "undisclosed"
        events.append(TimelineEvent(
            date=r["transaction_date"],
            event_type="Political Donation",
            description=f"{r['donor_name']} donated {amt} to {r['recipient_name']} ({r['recipient_party'] or ''})",
            source="FEC",
        ))

    # Board memberships
    rows = database.execute(
        """SELECT person_name, company_name, role, start_date, end_date
           FROM board_memberships WHERE person_name LIKE ? AND start_date IS NOT NULL""",
        (q,),
    )
    for r in rows:
        end = r["end_date"] or "present"
        events.append(TimelineEvent(
            date=r["start_date"],
            event_type="Board Appointment",
            description=f"{r['person_name']} joined {r['company_name']} as {r['role'] or 'Board Member'} (until {end})",
            source=r.get("source", "Board Records"),
        ))

    # UAP hearing mentions
    rows = database.execute(
        "SELECT title, date, summary FROM hearing_transcripts WHERE (witnesses LIKE ? OR summary LIKE ?) AND date IS NOT NULL",
        (q, q),
    )
    for r in rows:
        events.append(TimelineEvent(
            date=r["date"],
            event_type="Congressional Hearing Mention",
            description=f"Mentioned in: {r['title']}",
            source="Congress",
        ))

    # Political events (GDELT) actor mentions
    rows = database.execute(
        """SELECT event_date, event_description, actor1_country, source_url
           FROM political_events WHERE (actor1 LIKE ? OR actor2 LIKE ? OR event_description LIKE ?)
           AND event_date IS NOT NULL LIMIT 50""",
        (q, q, q),
    )
    for r in rows:
        events.append(TimelineEvent(
            date=r["event_date"],
            event_type="Political Event",
            description=r["event_description"] or "Political event",
            source="GDELT",
            url=r["source_url"],
        ))

    # News feed mentions
    rows = database.execute(
        "SELECT title, published_at, source, url FROM feed_items WHERE title LIKE ? AND published_at IS NOT NULL LIMIT 30",
        (q,),
    )
    for r in rows:
        events.append(TimelineEvent(
            date=r["published_at"][:10] if r["published_at"] else "",
            event_type="News Mention",
            description=r["title"],
            source=r["source"],
            url=r["url"],
        ))

    # Sort chronologically
    events.sort(key=lambda e: e.date or "", reverse=True)
    return events
