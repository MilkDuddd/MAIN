"""Board of directors cross-reference tracker.

Tracks overlapping board memberships — a key indicator of power network connections.
Uses Wikipedia infobox scraping and OpenCorporates officer data.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

from core import database, http_client
from models.power import BoardMember

_WIKI_API = "https://en.wikipedia.org/w/api.php"


def fetch_company_board_wikipedia(company_name: str) -> list[BoardMember]:
    """
    Attempt to extract board members from a company's Wikipedia infobox.
    """
    try:
        # First, search for the Wikipedia page
        search_resp = http_client.get(
            _WIKI_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": company_name,
                "format": "json",
                "srlimit": 1,
            },
            source="Wikipedia",
            timeout=15,
        )
        results = search_resp.json().get("query", {}).get("search", [])
        if not results:
            return []

        page_title = results[0]["title"]
        # Fetch page HTML
        page_resp = http_client.get(
            _WIKI_API,
            params={
                "action": "parse",
                "page": page_title,
                "prop": "text",
                "format": "json",
            },
            source="Wikipedia",
            timeout=20,
        )
        html = page_resp.json().get("parse", {}).get("text", {}).get("*", "")
        soup = BeautifulSoup(html, "html.parser")
        infobox = soup.find("table", class_=lambda c: c and "infobox" in c)
        if not infobox:
            return []

        members: list[BoardMember] = []
        for row in infobox.find_all("tr"):
            header = row.find("th")
            if not header:
                continue
            header_text = header.get_text(strip=True).lower()
            if any(kw in header_text for kw in ["board", "director", "officer", "executive", "chairman", "ceo", "cfo", "coo"]):
                value_td = row.find("td")
                if value_td:
                    names = [a.get_text(strip=True) for a in value_td.find_all("a")]
                    if not names:
                        names = [value_td.get_text(strip=True)]
                    for name in names:
                        if name and len(name) > 2:
                            members.append(BoardMember(
                                person_name=name,
                                company_name=company_name,
                                role=header.get_text(strip=True),
                                source="Wikipedia",
                            ))
        return members
    except Exception:
        return []


def save_to_db(members: list[BoardMember]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (m.person_name, m.company_name, m.role, m.start_date, m.end_date, m.source, now)
        for m in members
    ]
    database.execute_many(
        """INSERT INTO board_memberships
        (person_name, company_name, role, start_date, end_date, source, collected_at)
        VALUES (?,?,?,?,?,?,?)""",
        rows,
    )


def search_by_person(name: str) -> list[BoardMember]:
    """Find all board positions held by a person."""
    rows = database.execute(
        "SELECT * FROM board_memberships WHERE person_name LIKE ? ORDER BY company_name",
        (f"%{name}%",),
    )
    return [
        BoardMember(
            person_name=r["person_name"], company_name=r["company_name"],
            role=r["role"], start_date=r["start_date"],
            end_date=r["end_date"], source=r["source"],
        )
        for r in rows
    ]


def search_by_company(company: str) -> list[BoardMember]:
    """Find all board members for a company."""
    rows = database.execute(
        "SELECT * FROM board_memberships WHERE company_name LIKE ? ORDER BY person_name",
        (f"%{company}%",),
    )
    return [
        BoardMember(
            person_name=r["person_name"], company_name=r["company_name"],
            role=r["role"], start_date=r["start_date"],
            end_date=r["end_date"], source=r["source"],
        )
        for r in rows
    ]


def find_shared_boards(person1: str, person2: str) -> list[str]:
    """Find companies where two people share board membership."""
    boards1 = {m.company_name for m in search_by_person(person1)}
    boards2 = {m.company_name for m in search_by_person(person2)}
    return sorted(boards1 & boards2)
