"""
Radio driver package.

Three interchangeable drivers — all implement the same BaseRadio interface:

  SX127xRadio    – Direct SPI to SX1276/SX1278 chips (Raspberry Pi + HAT)
  SerialLoRa     – AT-command UART modules (RYLR998, EBYTE E22/E32, RAK811)
  SimulatorRadio – UDP loopback simulator for development without hardware

Usage
-----
    from radio import make_radio
    radio = make_radio("sx127x")   # or "serial" or "sim"
    radio.start()
    radio.send(raw_bytes)
    pkt = radio.recv(timeout=2.0)
    radio.stop()
"""

from .base import BaseRadio

def make_radio(driver: str, **kwargs) -> "BaseRadio":
    """
    Factory function.

    driver: "sx127x" | "serial" | "sim"
    kwargs: passed directly to the driver constructor.
    """
    driver = driver.lower()
    if driver in ("sx127x", "sx1276", "sx1278"):
        from .lora_sx127x import SX127xRadio
        return SX127xRadio(**kwargs)
    elif driver in ("serial", "at", "uart"):
        from .serial_lora import SerialLoRa
        return SerialLoRa(**kwargs)
    elif driver in ("sim", "simulator", "test"):
        from .simulator import SimulatorRadio
        return SimulatorRadio(**kwargs)
    else:
        raise ValueError(f"Unknown radio driver: {driver!r}. Use 'sx127x', 'serial', or 'sim'.")

__all__ = ["BaseRadio", "make_radio"]
