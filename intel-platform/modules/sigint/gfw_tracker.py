"""Global Fishing Watch — vessel tracking, dark vessel detection, IUU fishing flags."""
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from core import database, settings
from core.config import GFW_API
from core.http_client import get


def _headers() -> dict:
    key = settings.get("gfw_key", "")
    return {"Authorization": f"Bearer {key}"} if key else {}


def search_vessels(mmsi: Optional[str] = None, flag: Optional[str] = None,
                   vessel_name: Optional[str] = None) -> list[dict]:
    """Search vessels in GFW registry."""
    headers = _headers()
    if not headers:
        return [{"error": "GFW API key required. Run: intel settings set gfw_key YOUR_KEY"}]

    params: dict = {}
    if mmsi:
        params["ids"] = mmsi
    if flag:
        params["flag"] = flag
    if vessel_name:
        params["query"] = vessel_name

    vessels = []
    try:
        resp = get(f"{GFW_API}/vessels/search", params=params, headers=headers, timeout=20)
        if resp.status_code != 200:
            return [{"error": f"HTTP {resp.status_code}"}]
        data = resp.json()
        for v in data.get("vessels", []):
            vessels.append({
                "mmsi": v.get("registryInfo", [{}])[0].get("ssvid", "") if v.get("registryInfo") else "",
                "vessel_name": v.get("selfReportedInfo", [{}])[0].get("shipname", "") if v.get("selfReportedInfo") else "",
                "flag": v.get("registryInfo", [{}])[0].get("flag", "") if v.get("registryInfo") else "",
                "vessel_class": v.get("matchCriteria", ""),
                "imo": v.get("registryInfo", [{}])[0].get("imo", "") if v.get("registryInfo") else "",
                "gfw_id": v.get("id", ""),
            })
    except Exception as e:
        vessels = [{"error": str(e)}]
    return vessels


def get_vessel_tracks(gfw_vessel_id: str, days_back: int = 30) -> list[dict]:
    """Get recent track data for a vessel."""
    headers = _headers()
    if not headers:
        return []
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days_back)
    params = {
        "startDate": start_dt.strftime("%Y-%m-%d"),
        "endDate": end_dt.strftime("%Y-%m-%d"),
        "datasets": "public-global-fishing-tracks:latest",
    }
    tracks = []
    try:
        resp = get(f"{GFW_API}/events",
                   params={**params, "vessels": gfw_vessel_id},
                   headers=headers, timeout=30)
        if resp.status_code == 200:
            for event in resp.json().get("entries", []):
                tracks.append({
                    "event_type": event.get("type", ""),
                    "start": event.get("start", ""),
                    "end": event.get("end", ""),
                    "lat": event.get("position", {}).get("lat"),
                    "lon": event.get("position", {}).get("lon"),
                    "port_name": event.get("port", {}).get("name", "") if event.get("port") else "",
                    "fishing_hours": event.get("fishing", {}).get("totalDistanceKm", 0) if event.get("fishing") else 0,
                })
    except Exception:
        pass
    return tracks


def update_vessel_tracks_gfw(mmsi: str) -> dict:
    """Search vessel by MMSI and update DB with GFW intelligence."""
    vessels = search_vessels(mmsi=mmsi)
    if not vessels or "error" in vessels[0]:
        return {"error": vessels[0].get("error", "Not found") if vessels else "No results"}

    now = datetime.now(timezone.utc).isoformat()
    for v in vessels:
        if "error" in v:
            continue
        # Update/supplement existing vessel_tracks record
        existing = database.execute(
            "SELECT id FROM vessel_tracks WHERE mmsi=? ORDER BY collected_at DESC LIMIT 1",
            (v["mmsi"],),
        )
        if existing:
            database.execute_write(
                "UPDATE vessel_tracks SET name=?, flag=?, collected_at=? WHERE mmsi=?",
                (v["vessel_name"], v["flag"], now, v["mmsi"]),
            )
        else:
            database.execute_write(
                """INSERT INTO vessel_tracks
                   (mmsi, name, flag, callsign, vessel_type, collected_at)
                   VALUES (?,?,?,?,?,?)""",
                (v["mmsi"], v["vessel_name"], v["flag"], "", 0, now),
            )
    return {"vessels_found": len(vessels)}
