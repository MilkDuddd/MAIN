"""
Abstract base class for all radio drivers.

Every driver must implement:
  start()  – initialise hardware / open socket
  stop()   – release hardware / close socket
  send()   – transmit raw bytes
  recv()   – blocking receive with optional timeout

The mesh layer operates exclusively through this interface so drivers are
fully interchangeable.
"""

import abc
from typing import Optional, Tuple


class BaseRadio(abc.ABC):
    """Common interface for LoRa radio drivers."""

    @abc.abstractmethod
    def start(self) -> None:
        """Initialise the radio. Must be called before send/recv."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Release all hardware resources."""

    @abc.abstractmethod
    def send(self, data: bytes) -> None:
        """
        Transmit raw bytes over the air.

        Blocks until transmission is complete (or times out).
        Raises RadioError on failure.
        """

    @abc.abstractmethod
    def recv(self, timeout: Optional[float] = None) -> Optional[Tuple[bytes, int, float]]:
        """
        Wait for an incoming packet.

        Returns (raw_bytes, rssi_dBm, snr_dB) or None on timeout.
        Raises RadioError on hardware failure.
        """

    @property
    def is_open(self) -> bool:
        return False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()


class RadioError(IOError):
    """Raised when a radio operation fails."""
