"""AI-powered pattern analysis of entity profiles and intelligence data."""

import json
from typing import Generator, Optional

from core import ai_engine
from models.correlation import EntityProfile


def analyze_entity(profile: EntityProfile, stream: bool = True) -> Generator[str, None, None]:
    """Generate Groq AI analysis of an entity's intelligence profile."""
    context = _serialize_profile(profile)
    prompt = f"""Analyze the following intelligence profile for: {profile.entity.canonical_name}

Provide:
1. **Identity Summary** — who this entity is and why they matter
2. **Key Relationships** — most significant connections and what they imply
3. **Power Network** — corporate, financial, and political influence
4. **Risk Indicators** — sanctions, controversies, concerning patterns
5. **Timeline Highlights** — most significant dated events
6. **Intelligence Gaps** — what data is missing that would be important
7. **Assessment** — overall intelligence significance (1-10) with justification

Be factual. Distinguish clearly between confirmed data and inferences.
"""
    yield from ai_engine.analyze(prompt, context=context, stream=stream)


def analyze_connections(entity1: str, entity2: str) -> Generator[str, None, None]:
    """Analyze the relationship between two entities."""
    # Pull profiles for both
    from modules.correlation.entity_resolver import build_profile
    p1 = build_profile(entity1)
    p2 = build_profile(entity2)

    context = json.dumps({
        "entity1": _serialize_profile(p1),
        "entity2": _serialize_profile(p2),
    }, indent=2)[:6000]

    prompt = f"""Analyze the intelligence relationship between {entity1} and {entity2}.

Identify:
1. Direct connections (shared boards, donations, business relationships)
2. Indirect connections (mutual associates, shared organizations)
3. Potential conflicts of interest
4. Timeline of interactions
5. Intelligence significance of this relationship
"""
    yield from ai_engine.analyze(prompt, context=context)


def analyze_pattern(topic: str, data_json: str) -> Generator[str, None, None]:
    """Analyze patterns in raw intelligence data on a topic."""
    prompt = f"""Analyze the following intelligence data on the topic: {topic}

Identify:
1. Key patterns and anomalies
2. Hidden connections or implications
3. What this data suggests about the broader picture
4. Confidence level of each finding
5. Recommended follow-up intelligence collection
"""
    yield from ai_engine.analyze(prompt, context=data_json[:6000])


def _serialize_profile(profile: EntityProfile) -> str:
    """Serialize an EntityProfile to JSON string for AI context."""
    data = {
        "entity": {
            "id": profile.entity.entity_id,
            "name": profile.entity.canonical_name,
            "type": profile.entity.entity_type,
            "aliases": profile.entity.aliases,
            "sources": profile.entity.source_modules,
        },
        "relationships_count": len(profile.relationships),
        "sanctions": [
            {"list": s.list_source, "name": s.name, "reason": s.reason, "nationality": s.nationality}
            for s in profile.sanctions[:5]
        ],
        "political_donations": [
            {"to": d.recipient_name, "party": d.recipient_party, "amount": d.amount_usd, "date": d.transaction_date}
            for d in profile.donations[:10]
        ],
        "board_roles": [
            {"company": b.company_name, "role": b.role}
            for b in profile.board_roles[:10]
        ],
        "corporations": [
            {"name": c.name, "jurisdiction": c.jurisdiction, "type": c.company_type}
            for c in profile.corporations[:5]
        ],
        "uap_mentions": len(profile.uap_mentions),
        "recent_news": [
            {"title": n.title if hasattr(n, "title") else str(n)}
            for n in profile.news_items[:5]
        ],
    }
    return json.dumps(data, indent=2, default=str)
