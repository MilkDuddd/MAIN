"""Declassified UAP document tracker.

Aggregates links and metadata for known declassified UAP documents:
- CIA CREST database entries
- DIA reports (SunStreak/StarGate/LIFEBLOOD)
- Navy UAP reports
- AARO Historical Record Reports
- NSA Technical Journal articles on UAP
- Wilson-Davis memo
"""

import json
from datetime import datetime, timezone

from core import database
from models.uap import UAPReport

# Curated list of significant declassified/public UAP documents
_DOCUMENTS: list[dict] = [
    {
        "report_id": "AARO-HRR-VOL1-2024",
        "source": "AARO",
        "title": "AARO Historical Record Report Volume 1",
        "report_date": "2024-03-08",
        "classification": "Unclassified",
        "summary": "AARO's review of USG UAP programs since 1945. Found no verifiable evidence of extraterrestrial spacecraft or non-human intelligence programs. Reviewed 800+ UAP reports. Identified numerous misidentified mundane objects.",
        "document_url": "https://www.aaro.mil/Portals/136/PDFs/AARO_Historical_Record_Report_Vol_1_2024.pdf",
    },
    {
        "report_id": "DNI-UAPTF-2021",
        "source": "ODNI",
        "title": "Preliminary Assessment: Unidentified Aerial Phenomena",
        "report_date": "2021-06-25",
        "classification": "Unclassified",
        "summary": "First official public UAPTF report. Covered 144 UAP reports from 2004-2021. 143 remained unexplained. Described UAP as potential threat to flight safety and national security. 11 near-misses documented.",
        "document_url": "https://www.dni.gov/files/ODNI/documents/assessments/Prelimary-Assessment-UAP-20210625.pdf",
    },
    {
        "report_id": "NAVY-UAP-2019-GIMBAL",
        "source": "US Navy",
        "title": "Declassified UAP Video: Gimbal (2015)",
        "report_date": "2019-09-18",
        "classification": "Unclassified (Declassified)",
        "summary": "Declassified infrared video from USS Theodore Roosevelt (2015) showing a rotating UAP off US East Coast. Object appears to rotate and travel against the wind. No propulsion visible. Released officially by DoD.",
        "document_url": "https://www.navair.navy.mil/foia/documents",
    },
    {
        "report_id": "CIA-ROBERTSON-1953",
        "source": "CIA",
        "title": "Report of Scientific Panel on Unidentified Flying Objects (Robertson Panel)",
        "report_date": "1953-01-17",
        "classification": "Declassified",
        "summary": "CIA-sponsored scientific panel concluded UFOs posed no direct threat but recommended debunking public interest to reduce 'clogging' of intelligence channels. Led to Project Blue Book public relations strategy.",
        "document_url": "https://www.cia.gov/readingroom/docs/CIA-RDP81R00560R000100010001-9.pdf",
    },
    {
        "report_id": "DIA-LIFEBLOOD-2010",
        "source": "DIA",
        "title": "Advanced Aerospace Weapon System Applications (AAWSA) Program Reports",
        "report_date": "2010-01-01",
        "classification": "Unclassified (Partially Declassified)",
        "summary": "38 DIA technical reports commissioned under AATIP/AAWSA. Topics include: warp drives, traversable wormholes, dark energy, antigravity, directed energy weapons, invisibility cloaking, and biomaterial from UAP encounters.",
        "document_url": "https://documents.theblackvault.com/documents/ufos/aatip/",
    },
    {
        "report_id": "WILSON-DAVIS-MEMO-2002",
        "source": "Whistleblower",
        "title": "Wilson-Davis Notes (Eric Davis / Thomas Wilson)",
        "report_date": "2002-10-16",
        "classification": "Leaked/Unverified",
        "summary": "Alleged meeting notes between astrophysicist Eric Davis and Admiral Thomas Wilson. Claims Wilson was denied access to a private aerospace UAP reverse-engineering program. Authenticity disputed but widely circulated in UAP research community.",
        "document_url": "https://documents.theblackvault.com/documents/ufos/wilsondavis/",
    },
    {
        "report_id": "PROJECT-BLUEBOOK-FINAL",
        "source": "USAF",
        "title": "Project Blue Book Final Report (Condon Report)",
        "report_date": "1969-01-08",
        "classification": "Unclassified",
        "summary": "University of Colorado study commissioned by USAF. Concluded further study of UFOs unlikely to yield scientific advances. Led to closure of Project Blue Book. 21-30% of cases remained unexplained even after study.",
        "document_url": "https://www.nap.edu/catalog/24771/",
    },
    {
        "report_id": "NSA-COMINT-UAP-1980",
        "source": "NSA",
        "title": "NSA COMINT Report: UFO Hypothesis and Survival Questions",
        "report_date": "1980-01-01",
        "classification": "Declassified (2012)",
        "summary": "Declassified NSA technical journal article discussing implications if UFOs are extraterrestrial. Discusses information hazards, psychological preparedness, and communications intercepts related to UAP.",
        "document_url": "https://www.nsa.gov/Portals/75/documents/news-features/declassified-documents/ufo/ufo_hypothesis.pdf",
    },
    {
        "report_id": "ARMY-UNIDENTIFIED-1947",
        "source": "USAF",
        "title": "Project Sign Report (USAF Technical Report F-TR-2274-IA)",
        "report_date": "1948-02-11",
        "classification": "Declassified",
        "summary": "First official USAF UFO investigation. Originally concluded some UAPs might be extraterrestrial. Report was suppressed by Gen. Hoyt Vandenberg who ordered interplanetary hypothesis removed. Replaced by Project Grudge.",
        "document_url": "https://archive.org/details/ProjectSign",
    },
]


def populate_db() -> None:
    """Load known declassified documents into the database."""
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            d["report_id"], d["source"], d["title"], d["report_date"],
            d["classification"], d["summary"], None, d["document_url"], now,
        )
        for d in _DOCUMENTS
    ]
    database.execute_many(
        """INSERT OR IGNORE INTO uap_reports
        (report_id, source, title, report_date, classification, summary, full_text, document_url, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def get_all() -> list[UAPReport]:
    rows = database.execute("SELECT * FROM uap_reports ORDER BY report_date DESC")
    return [
        UAPReport(
            report_id=r["report_id"], source=r["source"], title=r["title"],
            report_date=r["report_date"], classification=r["classification"],
            summary=r["summary"], document_url=r["document_url"],
        )
        for r in rows
    ]


def search(keyword: str) -> list[UAPReport]:
    q = f"%{keyword}%"
    rows = database.execute(
        "SELECT * FROM uap_reports WHERE title LIKE ? OR summary LIKE ? OR source LIKE ? ORDER BY report_date DESC",
        (q, q, q),
    )
    return [
        UAPReport(
            report_id=r["report_id"], source=r["source"], title=r["title"],
            report_date=r["report_date"], classification=r["classification"],
            summary=r["summary"], document_url=r["document_url"],
        )
        for r in rows
    ]
