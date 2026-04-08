"""Political donation tracking via FEC (Federal Election Commission) API."""

from datetime import datetime, timezone
from typing import Optional

from core import database, http_client, settings
from core.config import FEC_API
from models.power import Donation, DonationResult


def fetch_donations(entity_name: str, cycle: Optional[str] = None) -> DonationResult:
    """
    Search FEC API for political contributions by a donor name.
    FEC API key required (free registration at api.open.fec.gov).
    """
    key = settings.get("fec_api_key", "")
    if not key:
        return DonationResult(
            query=entity_name,
            error="No fec_api_key configured. Register free at https://api.open.fec.gov/developers/",
        )

    params: dict = {
        "api_key": key,
        "contributor_name": entity_name,
        "per_page": 100,
        "sort": "-contribution_receipt_date",
    }
    if cycle:
        params["two_year_transaction_period"] = cycle

    try:
        resp = http_client.get(
            f"{FEC_API}/schedules/schedule_a/",
            params=params,
            source="FEC",
            timeout=30,
        )
        data = resp.json()
        results = data.get("results", [])
        donations: list[Donation] = []
        total_amount = 0.0
        for r in results:
            amount = r.get("contribution_receipt_amount") or 0.0
            total_amount += amount
            donations.append(Donation(
                donor_name=r.get("contributor_name", entity_name),
                recipient_name=r.get("committee_name", ""),
                amount_usd=amount,
                donor_employer=r.get("contributor_employer"),
                donor_occupation=r.get("contributor_occupation"),
                recipient_party=r.get("party_full"),
                transaction_date=r.get("contribution_receipt_date"),
                election_cycle=str(r.get("two_year_transaction_period", "")),
                source="FEC",
            ))
        return DonationResult(
            query=entity_name,
            donations=donations,
            total_amount_usd=total_amount,
            total=len(donations),
        )
    except Exception as e:
        return DonationResult(query=entity_name, error=str(e))


def save_to_db(donations: list[Donation]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            d.donor_name, d.donor_employer, d.donor_occupation,
            d.recipient_name, d.recipient_party, d.amount_usd,
            d.transaction_date, d.election_cycle, d.source, now,
        )
        for d in donations
    ]
    database.execute_many(
        """INSERT INTO political_donations
        (donor_name, donor_employer, donor_occupation, recipient_name,
         recipient_party, amount_usd, transaction_date, election_cycle, source, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(entity: str) -> DonationResult:
    """Query cached donations from the database."""
    q = f"%{entity}%"
    rows = database.execute(
        """SELECT * FROM political_donations
           WHERE donor_name LIKE ? OR recipient_name LIKE ?
           ORDER BY amount_usd DESC LIMIT 200""",
        (q, q),
    )
    donations = [
        Donation(
            donor_name=r["donor_name"], recipient_name=r["recipient_name"],
            amount_usd=r["amount_usd"], donor_employer=r["donor_employer"],
            donor_occupation=r["donor_occupation"], recipient_party=r["recipient_party"],
            transaction_date=r["transaction_date"], election_cycle=r["election_cycle"],
            source=r["source"],
        )
        for r in rows
    ]
    total = sum(d.amount_usd or 0 for d in donations)
    return DonationResult(query=entity, donations=donations, total_amount_usd=total, total=len(donations))
