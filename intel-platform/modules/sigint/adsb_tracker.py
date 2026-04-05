"""ADS-B flight tracking via OpenSky Network (free, no key required)."""

import json
from datetime import datetime, timezone
from typing import Optional

from core import database, http_client
from core.config import OPENSKY_URL
from models.sigint import FlightTrack, FlightResult


def fetch_flights(
    bbox: Optional[tuple[float, float, float, float]] = None,  # (lat_min, lon_min, lat_max, lon_max)
    callsign: Optional[str] = None,
    country: Optional[str] = None,
) -> FlightResult:
    """
    Fetch current live flights from OpenSky Network.
    bbox: (lat_min, lon_min, lat_max, lon_max)
    """
    params: dict = {}
    if bbox:
        params["lamin"] = bbox[0]
        params["lomin"] = bbox[1]
        params["lamax"] = bbox[2]
        params["lomax"] = bbox[3]

    try:
        resp = http_client.get(
            f"{OPENSKY_URL}/states/all",
            params=params,
            source="OpenSky",
            timeout=30,
        )
        data = resp.json()
        states = data.get("states") or []
        flights: list[FlightTrack] = []
        now_ts = datetime.now(timezone.utc).isoformat()

        for s in states:
            # OpenSky state vector format:
            # [icao24, callsign, origin_country, time_position, last_contact,
            #  longitude, latitude, baro_altitude, on_ground, velocity,
            #  true_track, vertical_rate, sensors, geo_altitude, squawk,
            #  spi, position_source, ...]
            if len(s) < 17:
                continue
            cs = (s[1] or "").strip()
            if callsign and callsign.upper() not in cs.upper():
                continue
            orig = s[2] or ""
            if country and country.upper() not in orig.upper():
                continue

            flights.append(FlightTrack(
                icao24=s[0] or "",
                callsign=cs or None,
                origin_country=orig or None,
                latitude=s[6],
                longitude=s[5],
                altitude_m=s[7],
                velocity_ms=s[9],
                true_track=s[10],
                vertical_rate=s[11],
                on_ground=bool(s[8]),
                squawk=s[14],
                collected_at=now_ts,
            ))

        return FlightResult(
            bbox=bbox,
            callsign_filter=callsign,
            flights=flights,
            total=len(flights),
        )
    except Exception as e:
        return FlightResult(bbox=bbox, callsign_filter=callsign, error=str(e))


def update_flights() -> None:
    """Scheduled job: snapshot current flight positions to database."""
    result = fetch_flights()
    if result.error or not result.flights:
        return
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            f.icao24, f.callsign, f.origin_country, f.latitude, f.longitude,
            f.altitude_m, f.velocity_ms, f.true_track, f.vertical_rate,
            1 if f.on_ground else 0, f.squawk, now,
        )
        for f in result.flights[:500]  # limit db writes per cycle
    ]
    database.execute_many(
        """INSERT INTO flight_tracks
        (icao24, callsign, origin_country, latitude, longitude, altitude_m,
         velocity_ms, true_track, vertical_rate, on_ground, squawk, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(callsign: Optional[str] = None, country: Optional[str] = None, limit: int = 200) -> FlightResult:
    """Query recent flight tracks from the database."""
    conditions = []
    params: list = []
    if callsign:
        conditions.append("callsign LIKE ?")
        params.append(f"%{callsign}%")
    if country:
        conditions.append("origin_country LIKE ?")
        params.append(f"%{country}%")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = database.execute(
        f"SELECT * FROM flight_tracks {where} ORDER BY collected_at DESC LIMIT ?",
        tuple(params) + (limit,),
    )
    flights = [
        FlightTrack(
            icao24=r["icao24"], callsign=r["callsign"], origin_country=r["origin_country"],
            latitude=r["latitude"], longitude=r["longitude"], altitude_m=r["altitude_m"],
            velocity_ms=r["velocity_ms"], true_track=r["true_track"],
            vertical_rate=r["vertical_rate"], on_ground=bool(r["on_ground"]),
            squawk=r["squawk"], collected_at=r["collected_at"],
        )
        for r in rows
    ]
    return FlightResult(callsign_filter=callsign, flights=flights, total=len(flights))
