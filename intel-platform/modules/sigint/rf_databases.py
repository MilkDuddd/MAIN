"""FCC ULS (Universal Licensing System) public RF spectrum database queries."""

from datetime import datetime, timezone
from typing import Optional

from core import database, http_client
from core.config import FCC_ULS_URL
from models.sigint import RFAllocation, RFResult


def fetch_fcc(callsign: Optional[str] = None, entity_name: Optional[str] = None, service: Optional[str] = None) -> RFResult:
    """
    Query FCC ULS public API for license information.
    API docs: https://www.fcc.gov/sites/default/files/public_access_api_v2.pdf
    """
    params: dict = {
        "format": "json",
        "status": "A",  # Active licenses
        "limit": 100,
    }
    if callsign:
        params["callsign"] = callsign.upper()
    if entity_name:
        params["licenseeName"] = entity_name
    if service:
        params["serviceGroup"] = service

    query_str = callsign or entity_name or service or "unknown"
    try:
        resp = http_client.get(FCC_ULS_URL, params=params, source="FCC ULS", timeout=30)
        data = resp.json()
        licenses = data.get("Licenses", {}).get("License", [])
        if isinstance(licenses, dict):
            licenses = [licenses]

        allocations: list[RFAllocation] = []
        for lic in licenses:
            # Parse frequency from channelList if available
            freq = None
            channels = lic.get("channelList", {}).get("channel", [])
            if channels:
                if isinstance(channels, dict):
                    channels = [channels]
                for ch in channels[:1]:
                    try:
                        freq = float(ch.get("freqLow", 0)) / 1000.0  # kHz to MHz
                    except (ValueError, TypeError):
                        pass

            allocations.append(RFAllocation(
                callsign=lic.get("callsign"),
                license_name=lic.get("licenseName"),
                entity_name=lic.get("licenseeName"),
                frequency_mhz=freq,
                service_type=lic.get("serviceDesc"),
                state=lic.get("licenseAddrState"),
                status=lic.get("statusDesc"),
                grant_date=lic.get("grantDate"),
                expiry_date=lic.get("expiredDate"),
                source="FCC",
            ))

        return RFResult(query=query_str, allocations=allocations)
    except Exception as e:
        return RFResult(query=query_str, error=str(e))


def save_to_db(result: RFResult) -> None:
    """Persist RF allocations to the database."""
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            a.callsign, a.license_name, a.entity_name, a.frequency_mhz,
            a.service_type, a.state, None, a.status, a.grant_date,
            a.expiry_date, a.source, now,
        )
        for a in result.allocations
    ]
    if rows:
        database.execute_many(
            """INSERT OR IGNORE INTO rf_allocations
            (callsign, license_name, entity_name, frequency_mhz, service_type,
             state, county, status, grant_date, expiry_date, source, collected_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows,
        )


def search_db(callsign: Optional[str] = None, entity: Optional[str] = None) -> RFResult:
    """Query cached RF allocations from the database."""
    conditions = []
    params: list = []
    if callsign:
        conditions.append("callsign LIKE ?")
        params.append(f"%{callsign}%")
    if entity:
        conditions.append("entity_name LIKE ?")
        params.append(f"%{entity}%")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = database.execute(
        f"SELECT * FROM rf_allocations {where} ORDER BY callsign LIMIT 200",
        tuple(params),
    )
    allocations = [
        RFAllocation(
            callsign=r["callsign"], license_name=r["license_name"],
            entity_name=r["entity_name"], frequency_mhz=r["frequency_mhz"],
            service_type=r["service_type"], state=r["state"],
            status=r["status"], grant_date=r["grant_date"],
            expiry_date=r["expiry_date"], source=r["source"],
        )
        for r in rows
    ]
    return RFResult(query=callsign or entity or "cached", allocations=allocations)
