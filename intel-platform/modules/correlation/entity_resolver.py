"""Entity resolution — deduplicate and link the same entity across data sources."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from core import database
from models.correlation import Entity, EntityProfile

try:
    from rapidfuzz import fuzz
    _HAS_RAPIDFUZZ = True
except ImportError:
    _HAS_RAPIDFUZZ = False


def _name_hash(name: str) -> str:
    """Normalize name to a stable hash for deduplication."""
    normalized = name.lower().strip()
    normalized = " ".join(sorted(normalized.split()))
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def get_or_create_entity(name: str, entity_type: str, source_module: str, aliases: Optional[list[str]] = None) -> Entity:
    """Find existing entity by name or create a new canonical entity."""
    now = datetime.now(timezone.utc).isoformat()
    entity_id = f"{entity_type[:3].upper()}-{_name_hash(name)}"

    # Check if entity exists
    rows = database.execute("SELECT * FROM entities WHERE entity_id=?", (entity_id,))
    if rows:
        row = rows[0]
        existing_aliases = json.loads(row["aliases"] or "[]")
        existing_modules = json.loads(row["source_modules"] or "[]")
        new_aliases = list(set(existing_aliases + (aliases or [])))
        new_modules = list(set(existing_modules + [source_module]))
        database.execute_write(
            "UPDATE entities SET aliases=?, source_modules=?, updated_at=? WHERE entity_id=?",
            (json.dumps(new_aliases), json.dumps(new_modules), now, entity_id),
        )
        return Entity(
            entity_id=entity_id,
            canonical_name=row["canonical_name"],
            entity_type=row["entity_type"],
            aliases=new_aliases,
            source_modules=new_modules,
        )

    # Create new entity
    entity = Entity(
        entity_id=entity_id,
        canonical_name=name,
        entity_type=entity_type,
        aliases=aliases or [],
        source_modules=[source_module],
        created_at=now,
        updated_at=now,
    )
    database.execute_write(
        """INSERT INTO entities (entity_id, canonical_name, entity_type, aliases, source_modules, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?)""",
        (entity_id, name, entity_type, json.dumps(aliases or []), json.dumps([source_module]), now, now),
    )
    return entity


def fuzzy_search_entities(query: str, threshold: int = 75) -> list[Entity]:
    """Search entities by fuzzy name match."""
    rows = database.execute("SELECT * FROM entities ORDER BY canonical_name")
    matches: list[tuple[int, Entity]] = []

    for row in rows:
        if _HAS_RAPIDFUZZ:
            score = fuzz.token_sort_ratio(query.lower(), row["canonical_name"].lower())
        else:
            # Fallback: simple substring match
            score = 100 if query.lower() in row["canonical_name"].lower() else 0

        if score >= threshold:
            aliases = json.loads(row["aliases"] or "[]")
            modules = json.loads(row["source_modules"] or "[]")
            entity = Entity(
                entity_id=row["entity_id"],
                canonical_name=row["canonical_name"],
                entity_type=row["entity_type"],
                aliases=aliases,
                source_modules=modules,
                notes=row["notes"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            matches.append((score, entity))

    matches.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in matches[:20]]


def add_relationship(source_id: str, target_id: str, rel_type: str,
                     confidence: float = 0.7, source_module: str = "", evidence: str = "") -> None:
    """Add a relationship between two entities."""
    now = datetime.now(timezone.utc).isoformat()
    # Check if relationship exists
    rows = database.execute(
        "SELECT id FROM relationships WHERE source_id=? AND target_id=? AND rel_type=?",
        (source_id, target_id, rel_type),
    )
    if rows:
        database.execute_write(
            "UPDATE relationships SET confidence=?, evidence=? WHERE id=?",
            (confidence, evidence, rows[0]["id"]),
        )
    else:
        database.execute_write(
            """INSERT INTO relationships (source_id, target_id, rel_type, confidence, source_module, evidence, created_at)
            VALUES (?,?,?,?,?,?,?)""",
            (source_id, target_id, rel_type, confidence, source_module, evidence, now),
        )


def build_profile(name: str) -> EntityProfile:
    """Aggregate cross-source data for a named entity."""
    # Find entity
    entities = fuzzy_search_entities(name, threshold=70)
    if not entities:
        # Try exact substring
        rows = database.execute(
            "SELECT * FROM entities WHERE canonical_name LIKE ?",
            (f"%{name}%",),
        )
        if not rows:
            from models.correlation import Entity as E
            entity = E(entity_id="", canonical_name=name, entity_type="person")
        else:
            r = rows[0]
            entity = Entity(
                entity_id=r["entity_id"],
                canonical_name=r["canonical_name"],
                entity_type=r["entity_type"],
                aliases=json.loads(r["aliases"] or "[]"),
                source_modules=json.loads(r["source_modules"] or "[]"),
            )
    else:
        entity = entities[0]

    # Pull relationships
    rel_rows = database.execute(
        "SELECT * FROM relationships WHERE source_id=? OR target_id=?",
        (entity.entity_id, entity.entity_id),
    )
    from models.correlation import Relationship
    relationships = [
        Relationship(
            source_id=r["source_id"], target_id=r["target_id"],
            rel_type=r["rel_type"], confidence=r["confidence"],
            source_module=r["source_module"], evidence=r["evidence"],
        )
        for r in rel_rows
    ]

    # Pull sanctions
    from modules.geopolitical.sanctions import search as sanction_search
    sanction_result = sanction_search(name)

    # Pull donations
    from modules.power.donations import search_db as donation_search
    donation_result = donation_search(name)

    # Pull board roles
    from modules.power.board_tracker import search_by_person
    board_roles = search_by_person(name)

    # Pull corps
    from modules.power.corporations import search_db as corp_search
    corp_result = corp_search(name)

    return EntityProfile(
        entity=entity,
        relationships=relationships,
        sanctions=sanction_result.matches,
        donations=donation_result.donations,
        board_roles=board_roles,
        corporations=corp_result.corporations,
    )
