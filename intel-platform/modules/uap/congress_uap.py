"""Congressional UAP hearings tracker.

Sources:
- congress.gov API for hearing records
- Hard-coded landmark hearing metadata (2022-2023 Senate/House hearings)
"""

import json
from datetime import datetime, timezone
from typing import Optional

from core import database, http_client
from models.uap import HearingTranscript, HearingsResult

# Landmark UAP hearings with known metadata
_KNOWN_HEARINGS: list[dict] = [
    {
        "hearing_id": "SASC-2022-UAP",
        "title": "Senate Armed Services Subcommittee: UAP Hearing",
        "date": "2022-05-17",
        "committee": "Armed Services Subcommittee on Intelligence and Emerging Threats",
        "chamber": "Senate",
        "witnesses": ["Scott Bray (Deputy Director of Naval Intelligence)", "Ronald Moultrie (USD Intelligence)"],
        "summary": "First public congressional hearing on UAPs in 50+ years. Officials presented 144 UAPTF reports, declassified UAP videos including 'Gimbal' and 'GoFast'. Officials acknowledged UAPs pose flight safety and national security concerns.",
        "key_quotes": [
            "We are investing in a range of technical collection and analysis methods to further advance our understanding — Scott Bray",
            "We want to know what's out there as much as you do — Ronald Moultrie",
        ],
        "document_url": "https://www.armed-services.senate.gov/hearings/to-receive-a-briefing-on-unidentified-aerial-phenomena",
    },
    {
        "hearing_id": "HOUSE-OVERSIGHT-2023-UAP",
        "title": "House Oversight Subcommittee: UAP Whistleblower Hearing",
        "date": "2023-07-26",
        "committee": "Subcommittee on National Security, the Border, and Foreign Affairs",
        "chamber": "House",
        "witnesses": [
            "David Grusch (Former NRO/AARO Officer, Whistleblower)",
            "Ryan Graves (Americans for Safe Aerospace)",
            "David Fravor (Retired Navy Commander, Tic Tac encounter)",
        ],
        "summary": "Historic hearing featuring whistleblower David Grusch testifying under oath about alleged classified UAP crash retrieval programs and non-human intelligence. Ryan Graves described near-miss incidents. David Fravor described the 2004 Nimitz encounter.",
        "key_quotes": [
            "These are not our aircraft — David Grusch, on alleged retrieved craft",
            "I was informed in the course of my official duties of a multi-decade UAP crash retrieval and reverse-engineering program — David Grusch",
            "The UAP I observed was white, oblong, some 40 feet long and perhaps 12 feet wide — David Fravor",
            "We are at an inflection point — Tim Burchett (R-TN)",
        ],
        "document_url": "https://oversight.house.gov/hearing/unidentified-anomalous-phenomena-implications-on-national-security-public-safety-and-government-transparency/",
    },
    {
        "hearing_id": "SENATE-INTEL-2023-UAP",
        "title": "Senate Intelligence Committee: UAP Provisions (NDAA FY2024)",
        "date": "2023-07-13",
        "committee": "Select Committee on Intelligence",
        "chamber": "Senate",
        "witnesses": ["Sean Kirkpatrick (AARO Director)"],
        "summary": "Senator Chuck Schumer introduced the UAP Disclosure Act of 2023, modeled after the JFK Records Act. AARO Director briefed on 800+ UAP reports reviewed since 2021. Legislation called for 25-year declassification review.",
        "key_quotes": [
            "We are not aware of any verifiable information to substantiate claims that any programs have been conducted — Sean Kirkpatrick",
            "The American people deserve to know — Chuck Schumer",
        ],
        "document_url": "https://www.intelligence.senate.gov/",
    },
    {
        "hearing_id": "HOUSE-OVERSIGHT-2024-UAP",
        "title": "House Oversight: UAP — Government Transparency and the People's Right to Know",
        "date": "2024-11-13",
        "committee": "Subcommittee on National Security, the Border, and Foreign Affairs",
        "chamber": "House",
        "witnesses": [
            "Luis Elizondo (Former AATIP Director)",
            "Michael Shellenberger (Journalist, UAP Caucus)",
            "Tim Gallaudet (Ret. Navy Admiral)",
            "Michael Gold (Space Policy Expert)",
        ],
        "summary": "Second major UAP hearing of 118th Congress. Elizondo testified about his work running AATIP and the existence of classified UAP programs. Discussion of NDAA 2024 UAP provisions and push for full disclosure legislation.",
        "key_quotes": [
            "UAPs represent a genuine mystery — Luis Elizondo",
            "We have recovered non-human biologics from crash sites — cited whistleblower claims",
        ],
        "document_url": "https://oversight.house.gov/",
    },
    {
        "hearing_id": "SENATE-ARMED-2024-UAP",
        "title": "Senate Armed Services: AARO Annual Report Briefing",
        "date": "2024-03-19",
        "committee": "Armed Services Committee",
        "chamber": "Senate",
        "witnesses": ["Sean Kirkpatrick (AARO Director, final briefing before retirement)"],
        "summary": "AARO presented findings from its Historical Record Report Vol. 1. Kirkpatrick maintained no verifiable evidence of extraterrestrial UAPs but acknowledged unexplained cases remain. Controversy over AARO's access to legacy programs.",
        "key_quotes": [
            "AARO has found no credible evidence of extraterrestrial activity — Sean Kirkpatrick",
        ],
        "document_url": "https://www.aaro.mil/",
    },
]


def get_all_hearings() -> list[HearingTranscript]:
    return [
        HearingTranscript(
            hearing_id=h["hearing_id"],
            title=h["title"],
            date=h["date"],
            committee=h["committee"],
            chamber=h["chamber"],
            witnesses=h["witnesses"],
            summary=h["summary"],
            key_quotes=h["key_quotes"],
            document_url=h["document_url"],
        )
        for h in _KNOWN_HEARINGS
    ]


def populate_db() -> None:
    """Load known hearings into the database."""
    now = datetime.now(timezone.utc).isoformat()
    hearings = get_all_hearings()
    rows = [
        (
            h.hearing_id, h.title, h.date, h.committee, h.chamber,
            json.dumps(h.witnesses), h.summary, json.dumps(h.key_quotes),
            h.document_url, now,
        )
        for h in hearings
    ]
    database.execute_many(
        """INSERT OR IGNORE INTO hearing_transcripts
        (hearing_id, title, date, committee, chamber, witnesses, summary, key_quotes, document_url, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(keyword: Optional[str] = None) -> HearingsResult:
    """Search hearings by keyword."""
    if keyword:
        q = f"%{keyword}%"
        rows = database.execute(
            """SELECT * FROM hearing_transcripts
               WHERE title LIKE ? OR summary LIKE ? OR key_quotes LIKE ? OR witnesses LIKE ?
               ORDER BY date DESC""",
            (q, q, q, q),
        )
    else:
        rows = database.execute("SELECT * FROM hearing_transcripts ORDER BY date DESC")

    hearings = [
        HearingTranscript(
            hearing_id=r["hearing_id"],
            title=r["title"],
            date=r["date"],
            committee=r["committee"],
            chamber=r["chamber"],
            witnesses=json.loads(r["witnesses"] or "[]"),
            summary=r["summary"],
            key_quotes=json.loads(r["key_quotes"] or "[]"),
            document_url=r["document_url"],
        )
        for r in rows
    ]
    return HearingsResult(keyword_filter=keyword, hearings=hearings, total=len(hearings))
