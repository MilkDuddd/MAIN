"""AIS vessel tracking via aisstream.io WebSocket API."""

import asyncio
import json
import threading
from datetime import datetime, timezone
from typing import Optional

from core import database, settings
from core.config import AISSTREAM_WS
from models.sigint import VesselTrack, VesselResult

# Vessel type codes to names (ITU/IMO standard)
_TYPE_MAP = {
    0: "Unknown", 20: "Wing in Ground", 21: "WIG Hazmat A", 22: "WIG Hazmat B",
    30: "Fishing", 31: "Towing", 32: "Towing (Large)", 33: "Dredging",
    34: "Diving", 35: "Military", 36: "Sailing", 37: "Pleasure Craft",
    40: "High Speed Craft", 50: "Pilot Vessel", 51: "SAR Vessel",
    52: "Tug", 53: "Port Tender", 54: "Anti-Pollution", 55: "Law Enforcement",
    58: "Medical Transport", 59: "Non-Combatant", 60: "Passenger",
    61: "Passenger Hazmat A", 70: "Cargo", 71: "Cargo Hazmat A",
    80: "Tanker", 81: "Tanker Hazmat A", 89: "Tanker Other",
    90: "Other",
}


def _parse_message(msg: dict) -> Optional[VesselTrack]:
    """Parse an AISstream position report message."""
    try:
        msg_type = msg.get("MessageType")
        meta = msg.get("MetaData", {})
        if msg_type == "PositionReport":
            pr = msg.get("Message", {}).get("PositionReport", {})
            return VesselTrack(
                mmsi=str(meta.get("MMSI", "")),
                name=meta.get("ShipName", "").strip(),
                callsign=meta.get("Callsign", "").strip() or None,
                latitude=pr.get("Latitude"),
                longitude=pr.get("Longitude"),
                sog=pr.get("Sog"),
                cog=pr.get("Cog"),
                heading=pr.get("TrueHeading"),
                flag=meta.get("country_iso"),
                collected_at=datetime.now(timezone.utc).isoformat(),
            )
        elif msg_type == "ShipStaticData":
            sd = msg.get("Message", {}).get("ShipStaticData", {})
            return VesselTrack(
                mmsi=str(meta.get("MMSI", "")),
                imo=str(sd.get("ImoNumber", "")) or None,
                name=sd.get("Name", "").strip(),
                callsign=sd.get("CallSign", "").strip() or None,
                vessel_type=sd.get("Type"),
                destination=sd.get("Destination", "").strip() or None,
                collected_at=datetime.now(timezone.utc).isoformat(),
            )
    except Exception:
        pass
    return None


def fetch_vessels_sync(
    bbox: Optional[tuple[float, float, float, float]] = None,
    mmsi: Optional[str] = None,
    duration_sec: int = 10,
) -> VesselResult:
    """
    Synchronously collect vessel positions from aisstream.io for duration_sec seconds.
    Requires aisstream_key in settings.
    """
    key = settings.get("aisstream_key", "")
    if not key:
        return VesselResult(query="aisstream", error="No aisstream_key configured")

    try:
        import websocket
    except ImportError:
        return VesselResult(query="aisstream", error="websocket-client not installed: pip install websocket-client")

    vessels: list[VesselTrack] = []
    subscribe_msg = {
        "APIKey": key,
        "BoundingBoxes": [],
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
    }
    if bbox:
        subscribe_msg["BoundingBoxes"] = [[
            {"Lat": bbox[0], "Lon": bbox[1]},
            {"Lat": bbox[2], "Lon": bbox[3]},
        ]]
    if mmsi:
        subscribe_msg["MMSI"] = [mmsi]

    received = threading.Event()
    timeout = duration_sec

    def on_message(ws, message):
        try:
            data = json.loads(message)
            v = _parse_message(data)
            if v:
                vessels.append(v)
        except Exception:
            pass

    def on_open(ws):
        ws.send(json.dumps(subscribe_msg))

    def on_error(ws, error):
        pass

    ws = websocket.WebSocketApp(
        AISSTREAM_WS,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
    )
    t = threading.Thread(target=ws.run_forever, daemon=True)
    t.start()
    t.join(timeout=timeout)
    ws.close()

    return VesselResult(
        query=f"bbox={bbox}" if bbox else (f"mmsi={mmsi}" if mmsi else "global"),
        vessels=vessels,
    )


def update_vessels() -> None:
    """Scheduled job: snapshot vessel positions."""
    result = fetch_vessels_sync(duration_sec=8)
    if not result.vessels:
        return
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            v.mmsi, v.imo, v.name, v.callsign, v.vessel_type, v.flag,
            v.latitude, v.longitude, v.sog, v.cog, v.heading,
            v.destination, v.eta, now,
        )
        for v in result.vessels[:300]
    ]
    database.execute_many(
        """INSERT INTO vessel_tracks
        (mmsi, imo, name, callsign, vessel_type, flag, latitude, longitude,
         sog, cog, heading, destination, eta, collected_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        rows,
    )


def search_db(mmsi: Optional[str] = None, country: Optional[str] = None, limit: int = 200) -> VesselResult:
    """Query recent vessel tracks from the database."""
    conditions = []
    params: list = []
    if mmsi:
        conditions.append("mmsi=?")
        params.append(mmsi)
    if country:
        conditions.append("flag LIKE ?")
        params.append(f"%{country}%")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = database.execute(
        f"SELECT * FROM vessel_tracks {where} ORDER BY collected_at DESC LIMIT ?",
        tuple(params) + (limit,),
    )
    vessels = [
        VesselTrack(
            mmsi=r["mmsi"], imo=r["imo"], name=r["name"], callsign=r["callsign"],
            vessel_type=r["vessel_type"], flag=r["flag"], latitude=r["latitude"],
            longitude=r["longitude"], sog=r["sog"], cog=r["cog"], heading=r["heading"],
            destination=r["destination"], eta=r["eta"], collected_at=r["collected_at"],
        )
        for r in rows
    ]
    return VesselResult(
        query=mmsi or country or "cached",
        vessels=vessels,
    )
