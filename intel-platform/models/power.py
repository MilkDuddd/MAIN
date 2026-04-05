"""Power structure data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Billionaire:
    name: str
    source_rank: Optional[int] = None
    net_worth_usd: Optional[float] = None
    source: str = "Forbes"
    country: Optional[str] = None
    industry: Optional[str] = None
    age: Optional[int] = None
    primary_company: Optional[str] = None
    wikidata_id: Optional[str] = None

    @property
    def net_worth_display(self) -> str:
        if self.net_worth_usd is None:
            return "N/A"
        b = self.net_worth_usd / 1e9
        return f"${b:.1f}B"


@dataclass
class BillionairesResult:
    country_filter: Optional[str] = None
    top_n: int = 100
    billionaires: list[Billionaire] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class Corporation:
    company_id: str
    name: str
    jurisdiction: Optional[str] = None
    company_type: Optional[str] = None
    incorporation_date: Optional[str] = None
    registered_address: Optional[str] = None
    status: Optional[str] = None
    parent_company_id: Optional[str] = None
    officers: list[dict] = field(default_factory=list)
    source: str = "OpenCorporates"


@dataclass
class CorpResult:
    query: str
    corporations: list[Corporation] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class BoardMember:
    person_name: str
    company_name: str
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source: Optional[str] = None


@dataclass
class Donation:
    donor_name: str
    recipient_name: str
    amount_usd: Optional[float] = None
    donor_employer: Optional[str] = None
    donor_occupation: Optional[str] = None
    recipient_party: Optional[str] = None
    transaction_date: Optional[str] = None
    election_cycle: Optional[str] = None
    source: str = "FEC"


@dataclass
class DonationResult:
    query: str
    donations: list[Donation] = field(default_factory=list)
    total_amount_usd: float = 0.0
    total: int = 0
    error: Optional[str] = None
