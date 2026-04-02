"""
Configuration for the encrypted LoRa radio system.

Hardware-agnostic settings. Radio-specific settings depend on the driver chosen:
  - SX127x (SPI):    Raspberry Pi + LoRa HAT/breakout (e.g. Adafruit, WaveShare)
  - Serial AT:       USB/UART LoRa modules  (RYLR998, EBYTE E22/E32, RAK811)
  - Simulator:       Local UDP sockets for testing without hardware
"""

from dataclasses import dataclass, field
from typing import Optional
import os

# ──────────────────────────────────────────────────────────
# Node identity
# ──────────────────────────────────────────────────────────

# 4-byte node ID (big-endian uint32). Set NODE_ID env var or change here.
# Must be unique on the network. 0xFFFFFFFF is the broadcast address.
NODE_ID: int = int(os.environ.get("NODE_ID", "1"))
NODE_ALIAS: str = os.environ.get("NODE_ALIAS", f"node-{NODE_ID}")

BROADCAST_ID: int = 0xFFFFFFFF

# ──────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────

KEYS_DIR: str = os.environ.get("KEYS_DIR", os.path.join(os.path.dirname(__file__), "keys"))

# ──────────────────────────────────────────────────────────
# SX127x (SPI) driver defaults
# Targets: Raspberry Pi + LoRa SX1276/SX1278 module
# ──────────────────────────────────────────────────────────

@dataclass
class SX127xConfig:
    # SPI bus & chip-select
    spi_bus: int = 0
    spi_device: int = 0
    spi_speed_hz: int = 5_000_000

    # GPIO BCM pin numbers
    reset_pin: int = 22
    dio0_pin: int = 4      # RxDone / TxDone interrupt

    # RF settings  ── tuned for maximum range ──
    # 433 MHz band: use 433.0e6  (check your regional regulations)
    # 868 MHz band: use 868.1e6  (Europe)
    # 915 MHz band: use 915.0e6  (Americas)
    frequency: float = 915.0e6

    # Spreading factor 7–12. SF12 = max range, ~250 bps.
    spreading_factor: int = 12

    # Signal bandwidth in Hz: 125000, 250000, 500000.
    # Narrower = longer range + slower data rate.
    bandwidth: int = 125_000

    # Coding rate denominator 5–8 (4/5 … 4/8). Higher = more FEC overhead.
    coding_rate: int = 8

    # TX output power in dBm (2–20 for PA_BOOST pin).
    tx_power: int = 20

    # Preamble length (symbols). Default 8 is fine.
    preamble_length: int = 8

    # CRC enabled on the LoRa packet
    crc_enabled: bool = True


# ──────────────────────────────────────────────────────────
# Serial AT-command LoRa module defaults
# Compatible: RYLR998, EBYTE E22/E32, RAK811, Heltec HT-CT62
# ──────────────────────────────────────────────────────────

@dataclass
class SerialLoRaConfig:
    port: str = os.environ.get("LORA_PORT", "/dev/ttyUSB0")
    baud: int = 115200
    timeout: float = 1.0

    # RF settings (applied via AT commands)
    frequency_mhz: float = 915.0
    spreading_factor: int = 12
    bandwidth_khz: int = 125       # 125 / 250 / 500
    coding_rate: int = 8           # 4/8
    tx_power_dbm: int = 22
    network_id: int = 18           # 0–16 (RYLR998 uses 0–16; 18 is private)
    address: int = NODE_ID & 0xFFFF  # 16-bit address for serial modules


# ──────────────────────────────────────────────────────────
# Simulator defaults
# ──────────────────────────────────────────────────────────

@dataclass
class SimulatorConfig:
    # All simulated nodes bind to localhost on different ports.
    # Port = BASE_PORT + node_id
    base_port: int = 54000
    host: str = "127.0.0.1"
    # Simulated packet loss 0.0–1.0
    packet_loss: float = 0.0
    # Simulated one-way latency in seconds
    latency: float = 0.05


# ──────────────────────────────────────────────────────────
# Mesh / protocol settings
# ──────────────────────────────────────────────────────────

@dataclass
class MeshConfig:
    # Maximum hop count before a packet is dropped.
    max_ttl: int = 7

    # How long (seconds) to remember seen message IDs (dedup cache).
    dedup_ttl: float = 60.0

    # ACK timeout in seconds. After this, message is considered lost.
    ack_timeout: float = 5.0

    # Number of retransmit attempts before giving up.
    max_retries: int = 3

    # Delay between retransmits (seconds).
    retry_delay: float = 2.0

    # Whether to relay overheard packets (mesh mode).
    relay: bool = True


# ──────────────────────────────────────────────────────────
# Defaults used by main.py when no CLI flags override them
# ──────────────────────────────────────────────────────────

DEFAULT_SX127X    = SX127xConfig()
DEFAULT_SERIAL    = SerialLoRaConfig()
DEFAULT_SIMULATOR = SimulatorConfig()
DEFAULT_MESH      = MeshConfig()
