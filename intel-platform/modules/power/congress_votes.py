"""ProPublica Congress API — voting records, bill sponsorship, member profiles."""
import json
from datetime import datetime, timezone
from typing import Optional

from core import database, settings
from core.config import PROPUBLICA_API
from core.http_client import get


def _headers() -> dict:
    key = settings.get("propublica_key", "")
    return {"X-API-Key": key} if key else {}


def get_member(name: str) -> list[dict]:
    """Search for a Congress member by name."""
    members = []
    for chamber in ("house", "senate"):
        try:
            resp = get(f"{PROPUBLICA_API}/members/{chamber}.json", headers=_headers(), timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json()
            all_members = data.get("results", [{}])[0].get("members", [])
            for m in all_members:
                full = f"{m.get('first_name','')} {m.get('last_name','')}".strip()
                if name.lower() in full.lower():
                    members.append({
                        "member_id": m.get("id", ""),
                        "full_name": full,
                        "party": m.get("party", ""),
                        "state": m.get("state", ""),
                        "chamber": chamber.title(),
                        "district": m.get("district", ""),
                        "in_office": 1 if m.get("in_office") else 0,
                        "dw_nominate": m.get("dw_nominate", None),
                        "twitter_account": m.get("twitter_account", ""),
                        "url": m.get("url", ""),
                    })
        except Exception:
            pass
    return members


def store_members(members: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for m in members:
        database.execute_write(
            """INSERT OR REPLACE INTO congress_members
               (member_id, full_name, party, state, chamber, district, in_office,
                dw_nominate, twitter_account, url, collected_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (m["member_id"], m["full_name"], m["party"], m["state"], m["chamber"],
             m.get("district"), m.get("in_office", 0), m.get("dw_nominate"),
             m.get("twitter_account", ""), m.get("url", ""), now),
        )


def get_votes(member_id: str, congress: int = 119) -> list[dict]:
    """Fetch recent votes for a member."""
    votes = []
    try:
        resp = get(f"{PROPUBLICA_API}/members/{member_id}/votes.json",
                   headers=_headers(), timeout=15)
        if resp.status_code != 200:
            return votes
        results = resp.json().get("results", [{}])[0].get("votes", [])
        for v in results[:100]:
            votes.append({
                "vote_id": f"{member_id}_{v.get('roll_call','')}_{v.get('congress','')}",
                "member_id": member_id,
                "member_name": "",
                "congress": v.get("congress"),
                "bill_id": v.get("bill", {}).get("bill_id", ""),
                "bill_title": v.get("bill", {}).get("title", ""),
                "vote_date": v.get("date", ""),
                "vote_position": v.get("position", ""),
                "result": v.get("result", ""),
            })
    except Exception:
        pass
    return votes


def store_votes(votes: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for v in votes:
        database.execute_write(
            """INSERT OR IGNORE INTO congress_votes
               (vote_id, member_id, member_name, congress, bill_id, bill_title,
                vote_date, vote_position, result, collected_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (v["vote_id"], v["member_id"], v["member_name"], v.get("congress"),
             v["bill_id"], v["bill_title"], v["vote_date"], v["vote_position"],
             v["result"], now),
        )


def search_and_store(name: str) -> list[dict]:
    members = get_member(name)
    if members:
        store_members(members)
    return members


def search_db(query: str) -> list[dict]:
    rows = database.execute(
        "SELECT * FROM congress_members WHERE full_name LIKE ? OR state LIKE ? ORDER BY full_name LIMIT 50",
        (f"%{query}%", f"%{query}%"),
    )
    return [dict(r) for r in rows]
