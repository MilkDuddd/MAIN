"""SIGINT data models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FlightTrack:
    icao24: str
    callsign: Optional[str] = None
    origin_country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    velocity_ms: Optional[float] = None
    true_track: Optional[float] = None   # heading degrees
    vertical_rate: Optional[float] = None
    on_ground: bool = False
    squawk: Optional[str] = None
    collected_at: Optional[str] = None

    @property
    def altitude_ft(self) -> Optional[float]:
        return round(self.altitude_m * 3.28084, 0) if self.altitude_m is not None else None

    @property
    def speed_knots(self) -> Optional[float]:
        return round(self.velocity_ms * 1.94384, 1) if self.velocity_ms is not None else None


@dataclass
class FlightResult:
    bbox: Optional[tuple] = None
    callsign_filter: Optional[str] = None
    flights: list[FlightTrack] = field(default_factory=list)
    total: int = 0
    error: Optional[str] = None


@dataclass
class VesselTrack:
    mmsi: str
    imo: Optional[str] = None
    name: Optional[str] = None
    callsign: Optional[str] = None
    vessel_type: Optional[int] = None
    flag: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sog: Optional[float] = None      # speed over ground, knots
    cog: Optional[float] = None      # course over ground, degrees
    heading: Optional[float] = None
    destination: Optional[str] = None
    eta: Optional[str] = None
    collected_at: Optional[str] = None

    @property
    def vessel_type_name(self) -> str:
        types = {
            0: "Unknown", 20: "Wing in Ground", 30: "Fishing",
            31: "Towing", 36: "Sailing", 37: "Pleasure Craft",
            40: "High Speed Craft", 50: "Pilot Vessel", 51: "Search & Rescue",
            52: "Tug", 60: "Passenger", 70: "Cargo", 80: "Tanker",
            90: "Other",
        }
        if self.vessel_type is None:
            return "Unknown"
        base = (self.vessel_type // 10) * 10
        return types.get(self.vessel_type, types.get(base, "Other"))


@dataclass
class VesselResult:
    query: str
    vessels: list[VesselTrack] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class RFAllocation:
    callsign: Optional[str] = None
    license_name: Optional[str] = None
    entity_name: Optional[str] = None
    frequency_mhz: Optional[float] = None
    service_type: Optional[str] = None
    state: Optional[str] = None
    county: Optional[str] = None
    status: Optional[str] = None
    grant_date: Optional[str] = None
    expiry_date: Optional[str] = None
    source: str = "FCC"


@dataclass
class RFResult:
    query: str
    allocations: list[RFAllocation] = field(default_factory=list)
    error: Optional[str] = None
