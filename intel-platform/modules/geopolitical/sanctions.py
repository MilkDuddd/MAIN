"""Sanctions list fetcher — OFAC SDN, EU Consolidated, UN Security Council."""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Optional
from xml.etree import ElementTree as ET

from core import database, http_client
from core.config import OFAC_SDN_XML, EU_SANCTIONS_XML, UN_SANCTIONS_URL
from models.geopolitical import Sanction, SanctionResult


# ── OFAC SDN ──────────────────────────────────────────────────────────────────

def _parse_ofac(xml_text: str) -> list[Sanction]:
    sanctions: list[Sanction] = []
    ns = {"ofac": ""}
    try:
        root = ET.fromstring(xml_text)
        # OFAC SDN XML namespace handling
        ns_match = re.match(r"\{([^}]+)\}", root.tag)
        ns_uri = ns_match.group(1) if ns_match else ""
        ns_prefix = f"{{{ns_uri}}}" if ns_uri else ""

        for entry in root.iter(f"{ns_prefix}sdnEntry"):
            uid = entry.findtext(f"{ns_prefix}uid", "")
            sdn_type = entry.findtext(f"{ns_prefix}sdnType", "")
            last = entry.findtext(f"{ns_prefix}lastName", "")
            first = entry.findtext(f"{ns_prefix}firstName", "")
            name = f"{first} {last}".strip() if first else last

            aliases: list[str] = []
            for aka in entry.iter(f"{ns_prefix}aka"):
                aka_last = aka.findtext(f"{ns_prefix}lastName", "")
                aka_first = aka.findtext(f"{ns_prefix}firstName", "")
                alias = f"{aka_first} {aka_last}".strip() if aka_first else aka_last
                if alias:
                    aliases.append(alias)

            programs: list[str] = []
            for prog in entry.iter(f"{ns_prefix}program"):
                if prog.text:
                    programs.append(prog.text)

            dob = entry.findtext(f".//{ns_prefix}dateOfBirth", "")
            nationality = entry.findtext(f".//{ns_prefix}nationality", "")

            sanction_id = f"OFAC-{uid}"
            sanctions.append(Sanction(
                sanction_id=sanction_id,
                list_source="OFAC",
                entity_type=sdn_type,
                name=name,
                aliases=aliases,
                nationality=nationality or None,
                date_of_birth=dob or None,
                programs=programs,
            ))
    except ET.ParseError:
        pass
    return sanctions


# ── UN Consolidated ───────────────────────────────────────────────────────────

def _parse_un(xml_text: str) -> list[Sanction]:
    sanctions: list[Sanction] = []
    try:
        root = ET.fromstring(xml_text)
        ns_match = re.match(r"\{([^}]+)\}", root.tag)
        ns_prefix = f"{{{ns_match.group(1)}}}" if ns_match else ""

        for individual in root.iter(f"{ns_prefix}INDIVIDUAL"):
            ref = individual.findtext(f"{ns_prefix}REFERENCE_NUMBER", "")
            first = individual.findtext(f"{ns_prefix}FIRST_NAME", "")
            second = individual.findtext(f"{ns_prefix}SECOND_NAME", "")
            third = individual.findtext(f"{ns_prefix}THIRD_NAME", "")
            name = " ".join(filter(None, [first, second, third]))

            aliases: list[str] = []
            for alias in individual.iter(f"{ns_prefix}ALIAS"):
                qa = alias.findtext(f"{ns_prefix}QUALITY", "")
                an = alias.findtext(f"{ns_prefix}ALIAS_NAME", "")
                if an:
                    aliases.append(an)

            nat = individual.findtext(f".//{ns_prefix}VALUE", "")
            dob_elem = individual.find(f".//{ns_prefix}DATE")
            dob = dob_elem.text if dob_elem is not None else None

            sanctions.append(Sanction(
                sanction_id=f"UN-{ref}",
                list_source="UN",
                entity_type="Individual",
                name=name,
                aliases=aliases,
                nationality=nat or None,
                date_of_birth=dob,
                reason=individual.findtext(f"{ns_prefix}COMMENTS1"),
            ))

        for entity in root.iter(f"{ns_prefix}ENTITY"):
            ref = entity.findtext(f"{ns_prefix}REFERENCE_NUMBER", "")
            name = entity.findtext(f"{ns_prefix}FIRST_NAME", "") or entity.findtext(f"{ns_prefix}ENTITY_NAME", "")
            sanctions.append(Sanction(
                sanction_id=f"UN-E-{ref}",
                list_source="UN",
                entity_type="Entity",
                name=name,
                reason=entity.findtext(f"{ns_prefix}COMMENTS1"),
            ))
    except ET.ParseError:
        pass
    return sanctions


def fetch_ofac() -> list[Sanction]:
    resp = http_client.get(OFAC_SDN_XML, source="OFAC", timeout=120)
    return _parse_ofac(resp.text)


def fetch_un() -> list[Sanction]:
    resp = http_client.get(UN_SANCTIONS_URL, source="UN Sanctions", timeout=120)
    return _parse_un(resp.text)


def update_sanctions() -> None:
    """Scheduled job: refresh sanctions databases."""
    now = datetime.now(timezone.utc).isoformat()
    all_sanctions: list[Sanction] = []

    for fetcher in (fetch_ofac, fetch_un):
        try:
            all_sanctions.extend(fetcher())
        except Exception:
            pass

    rows = [
        (
            s.sanction_id, s.list_source, s.entity_type, s.name,
            json.dumps(s.aliases), s.nationality, s.date_of_birth,
            s.reason, json.dumps(s.programs), s.effective_date, now,
        )
        for s in all_sanctions
    ]
    if rows:
        database.execute_many(
            """INSERT OR REPLACE INTO sanctions
            (sanction_id, list_source, entity_type, name, aliases, nationality,
             date_of_birth, reason, programs, effective_date, collected_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )


def search(query: str, list_source: Optional[str] = None) -> SanctionResult:
    """Search sanctions database by name (fuzzy via SQL LIKE)."""
    q = f"%{query}%"
    if list_source:
        rows = database.execute(
            "SELECT * FROM sanctions WHERE (name LIKE ? OR aliases LIKE ?) AND list_source=? ORDER BY name",
            (q, q, list_source),
        )
    else:
        rows = database.execute(
            "SELECT * FROM sanctions WHERE name LIKE ? OR aliases LIKE ? ORDER BY name",
            (q, q),
        )

    matches = [
        Sanction(
            sanction_id=r["sanction_id"],
            list_source=r["list_source"],
            entity_type=r["entity_type"],
            name=r["name"],
            aliases=json.loads(r["aliases"] or "[]"),
            nationality=r["nationality"],
            date_of_birth=r["date_of_birth"],
            reason=r["reason"],
            programs=json.loads(r["programs"] or "[]"),
            effective_date=r["effective_date"],
        )
        for r in rows
    ]
    return SanctionResult(query=query, matches=matches, total=len(matches))
