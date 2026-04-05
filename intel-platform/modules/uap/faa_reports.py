"""FAA incident and pilot report tracker for UAP-relevant aviation incidents."""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from core import database, http_client
from models.uap import UAPSighting, SightingsResult

# FAA Wildlife Strike Database (public) - closest public dataset to pilot UAP reports
FAA_WILDLIFE_URL = "https://wildlife.faa.gov/database.aspx"

# FAA ASRS (Aviation Safety Reporting System) — public summary reports
ASRS_URL = "https://asrs.arc.nasa.gov/search/database.html"

# Known documented FAA/pilot encounters with curated metadata
_DOCUMENTED_ENCOUNTERS: list[dict] = [
    {
        "report_id": "FAA-NIMITZ-2004",
        "source": "FAA/Navy",
        "occurred_date": "2004-11-14",
        "city": "Pacific Ocean",
        "state": "CA",
        "country": "US",
        "shape": "Tic Tac / Oblong",
        "duration_sec": 300,
        "description": "USS Nimitz Carrier Strike Group encounter. Cmdr. David Fravor and Lt. Cmdr. Jim Slaight of VFA-41 observed a 40-ft white oblong craft performing maneuvers impossible for known aircraft — no wings, no propulsion, hovering at 50,000 ft then rapidly accelerating. Multiple radar tracks by USS Princeton (CG-59). Video footage (FLIR1/'Tic Tac') later declassified by DoD.",
        "posted_url": "https://www.navair.navy.mil/foia/documents",
    },
    {
        "report_id": "FAA-ROOSEVELT-2014-2015",
        "source": "FAA/Navy",
        "occurred_date": "2014-08-01",
        "city": "Atlantic Ocean, Virginia/North Carolina coast",
        "state": "VA",
        "country": "US",
        "shape": "Sphere/Cube",
        "duration_sec": None,
        "description": "Multiple pilots from VFA-11 and VFA-106 on USS Theodore Roosevelt reported UAPs almost daily during 2014-2015 workups. Witnessed near-collisions, objects at 30,000 ft with no propulsion. Yielded 'Gimbal' and 'GoFast' declassified FLIR videos. Lt. Ryan Graves testified to Congress in 2023.",
        "posted_url": "https://www.dni.gov/files/ODNI/documents/assessments/Prelimary-Assessment-UAP-20210625.pdf",
    },
    {
        "report_id": "FAA-PHOENIX-LIGHTS-1997",
        "source": "FAA/Witnesses",
        "occurred_date": "1997-03-13",
        "city": "Phoenix",
        "state": "AZ",
        "country": "US",
        "shape": "V-shaped / Boomerang",
        "duration_sec": 7200,
        "description": "Thousands of witnesses including Governor Fife Symington observed a massive V-shaped craft traveling silently from Henderson NV through Phoenix AZ to Tucson AZ. FAA radar confirmed 'unidentified' traffic. Governor later admitted he saw the object and it was 'otherworldly.' Military initially attributed to A-10 flares (second event).",
        "posted_url": "https://nuforc.org",
    },
    {
        "report_id": "FAA-O'HARE-2006",
        "source": "FAA/United Airlines",
        "occurred_date": "2006-11-07",
        "city": "Chicago",
        "state": "IL",
        "country": "US",
        "shape": "Disc/Metallic",
        "duration_sec": 300,
        "description": "United Airlines employees including pilots and ground crew at O'Hare International Airport observed a metallic disc hovering at approximately 1,500 ft over Gate C17. Object shot upward through cloud layer leaving a 'hole.' FAA and NTSB declined investigation. Chicago Tribune FOIA obtained FAA audio recordings confirming the incident.",
        "posted_url": "https://www.faa.gov",
    },
    {
        "report_id": "FAA-CHANNEL-ISLANDS-2018",
        "source": "FAA/American Airlines",
        "occurred_date": "2018-02-24",
        "city": "Channel Islands airspace",
        "state": "AZ",
        "country": "US",
        "shape": "Unknown",
        "duration_sec": 60,
        "description": "American Airlines Flight 1095 crew reported a UAP with a 'big reflection' moving very fast pass overhead at 36,000 ft over Arizona near the Sonoran Desert. FAA radio communications confirmed. FBI later contacted the flight crew.",
        "posted_url": "https://www.faa.gov",
    },
]


def populate_db() -> None:
    """Load documented FAA-related encounters into the database."""
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            e["report_id"], e["source"], e["occurred_date"], None,
            e["city"], e["state"], e["country"], e["shape"],
            e["duration_sec"], e["description"], e["posted_url"],
            None, None, now,
        )
        for e in _DOCUMENTED_ENCOUNTERS
    ]
    database.execute_many(
        """INSERT OR IGNORE INTO uap_sightings
        (report_id, source, occurred_date, reported_date, city, state, country,
         shape, duration_sec, description, posted_url, lat, lon, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(keyword: Optional[str] = None) -> SightingsResult:
    """Query FAA-sourced UAP encounters from the database."""
    if keyword:
        rows = database.execute(
            "SELECT * FROM uap_sightings WHERE source LIKE '%FAA%' AND description LIKE ? ORDER BY occurred_date DESC",
            (f"%{keyword}%",),
        )
    else:
        rows = database.execute(
            "SELECT * FROM uap_sightings WHERE source LIKE '%FAA%' ORDER BY occurred_date DESC"
        )
    sightings = [
        UAPSighting(
            report_id=r["report_id"], source=r["source"],
            occurred_date=r["occurred_date"], city=r["city"],
            state=r["state"], country=r["country"], shape=r["shape"],
            duration_sec=r["duration_sec"], description=r["description"],
            posted_url=r["posted_url"],
        )
        for r in rows
    ]
    return SightingsResult(sightings=sightings, total=len(sightings))
