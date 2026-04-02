"""
Serial AT-command LoRa driver.

Compatible modules (all use similar AT command sets):
  RYLR998   – REYAX, 868/915 MHz, SX1276, UART
  RYLR406   – REYAX, 433 MHz, SX1278, UART
  EBYTE E22 – 868/915 MHz, SX1262, UART
  EBYTE E32 – 433/868/915 MHz, SX1278, UART
  RAK811    – 868/915 MHz, SX1276, UART
  Heltec HT-CT62 – 868/915 MHz, SX1262, UART

Wiring
──────
  Module TX  →  RPi RX  (GPIO 15, physical pin 10)
  Module RX  →  RPi TX  (GPIO 14, physical pin 8)
  Module VCC →  3.3 V or 5 V (check module specs)
  Module GND →  GND
  Module AUX →  GPIO (optional; indicates module busy)

Enable serial on Raspberry Pi:
  sudo raspi-config → Interface Options → Serial Port
  (disable login shell over serial, enable the hardware port)

AT command reference (RYLR998)
──────────────────────────────
  AT+RESET               hardware reset
  AT+VER?                firmware version
  AT+ADDRESS=<n>         set 16-bit node address
  AT+NETWORKID=<n>       0–16 (private: 18)
  AT+PARAMETER=<SF>,<BW>,<CR>,<PP>
                         SF=7-12, BW=0-9, CR=1-4, PP=4-25
  AT+BAND=<Hz>           carrier frequency in Hz
  AT+CRFOP=<dBm>         TX power 0–22
  AT+SEND=<addr>,<len>,<hex_data>
  +RCV=<addr>,<len>,<hex_data>,<rssi>,<snr>

EBYTE E22 differences
─────────────────────
  Uses AT+PARAMETER differently; see EBYTE E22 datasheet.
  This driver auto-detects the module family from the AT+VER? response.
"""

import re
import time
import threading
import queue
from typing import Optional, Tuple

import serial

from .base import BaseRadio, RadioError


# ──────────────────────────────────────────────────────────
# BW lookup tables
# ──────────────────────────────────────────────────────────

# RYLR998 / SX1276 bandwidth codes
RYLR_BW = {125: 7, 250: 8, 500: 9}
RYLR_BW_REV = {v: k for k, v in RYLR_BW.items()}


class SerialLoRa(BaseRadio):
    """
    Communicates with AT-command LoRa modules over UART/USB serial.
    Incoming packets are read by a background thread and placed on a queue.
    """

    def __init__(self, config=None):
        from config import SerialLoRaConfig
        self._cfg = config or SerialLoRaConfig()
        self._ser: Optional[serial.Serial] = None
        self._rx_queue: queue.Queue = queue.Queue()
        self._rx_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._open = False
        self._module_family = "rylr"   # "rylr" or "ebyte"

    # ── BaseRadio interface ────────────────────────────────

    def start(self) -> None:
        self._ser = serial.Serial(
            port=self._cfg.port,
            baudrate=self._cfg.baud,
            timeout=self._cfg.timeout,
        )
        time.sleep(0.5)   # let UART settle

        self._detect_module()
        self._configure_module()
        self._open = True

        self._running = True
        self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self._rx_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._rx_thread:
            self._rx_thread.join(timeout=3.0)
        if self._ser and self._ser.is_open:
            self._ser.close()
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    def send(self, data: bytes) -> None:
        """Send raw bytes via AT+SEND as hex-encoded payload."""
        if len(data) > 240:
            raise RadioError(f"Payload too long: {len(data)} bytes (max 240 for serial modules)")
        hex_data = data.hex().upper()
        addr = self._cfg.address & 0xFFFF
        cmd  = f"AT+SEND={addr},{len(data)},{hex_data}\r\n"
        with self._lock:
            self._write(cmd)
            resp = self._read_line(timeout=3.0)
            if resp and "+ERR" in resp:
                raise RadioError(f"AT+SEND failed: {resp.strip()}")

    def recv(self, timeout: Optional[float] = None) -> Optional[Tuple[bytes, int, float]]:
        try:
            return self._rx_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # ── Module auto-detection ──────────────────────────────

    def _detect_module(self) -> None:
        self._write("AT+VER?\r\n")
        resp = self._read_line(timeout=2.0) or ""
        if "RYLR" in resp.upper() or "REYAX" in resp.upper():
            self._module_family = "rylr"
        elif "EBYTE" in resp.upper() or "E22" in resp.upper():
            self._module_family = "ebyte"
        else:
            # Try basic AT ping
            self._write("AT\r\n")
            pong = self._read_line(timeout=1.0) or ""
            if "+OK" not in pong and "OK" not in pong:
                raise RadioError(
                    f"No response from LoRa module on {self._cfg.port}. "
                    "Check wiring and baud rate."
                )

    def _configure_module(self) -> None:
        cfg = self._cfg

        # Reset
        self._at_cmd("AT+RESET", timeout=3.0)
        time.sleep(1.0)

        if self._module_family == "rylr":
            self._configure_rylr(cfg)
        else:
            self._configure_ebyte(cfg)

    def _configure_rylr(self, cfg) -> None:
        bw_code = RYLR_BW.get(cfg.bandwidth_khz, 7)
        cr_code = cfg.coding_rate - 4   # 4/5→1, 4/8→4

        self._at_cmd(f"AT+ADDRESS={cfg.address & 0xFFFF}")
        self._at_cmd(f"AT+NETWORKID={cfg.network_id}")
        self._at_cmd(f"AT+BAND={int(cfg.frequency_mhz * 1_000_000)}")
        # SF, BW code, CR code, preamble (4–25 symbols)
        self._at_cmd(f"AT+PARAMETER={cfg.spreading_factor},{bw_code},{cr_code},12")
        self._at_cmd(f"AT+CRFOP={min(cfg.tx_power_dbm, 22)}")

    def _configure_ebyte(self, cfg) -> None:
        # EBYTE E22 AT command set (subset)
        self._at_cmd(f"AT+ADDRESS={cfg.address & 0xFFFF}")
        self._at_cmd(f"AT+NETWORKID={cfg.network_id}")
        freq_mhz = int(cfg.frequency_mhz)
        self._at_cmd(f"AT+BAND={freq_mhz}")
        self._at_cmd(f"AT+PARAMETER={cfg.spreading_factor},{cfg.bandwidth_khz},{cfg.coding_rate - 4},12")
        self._at_cmd(f"AT+CRFOP={min(cfg.tx_power_dbm, 22)}")

    # ── Background RX thread ───────────────────────────────

    def _rx_loop(self) -> None:
        while self._running:
            try:
                line = self._read_line(timeout=0.5)
                if line and line.startswith("+RCV="):
                    self._parse_rcv(line)
            except Exception:
                pass    # serial errors are transient; keep running

    def _parse_rcv(self, line: str) -> None:
        """
        Parse RYLR +RCV response:
          +RCV=<sender_addr>,<length>,<hex_data>,<rssi>,<snr>
        """
        m = re.match(
            r"\+RCV=(\d+),(\d+),([0-9A-Fa-f]+),(-?\d+),(-?[\d.]+)",
            line.strip(),
        )
        if not m:
            return
        hex_data = m.group(3)
        rssi     = int(m.group(4))
        snr      = float(m.group(5))
        try:
            data = bytes.fromhex(hex_data)
        except ValueError:
            return
        self._rx_queue.put((data, rssi, snr))

    # ── Serial helpers ─────────────────────────────────────

    def _write(self, text: str) -> None:
        self._ser.write(text.encode())
        self._ser.flush()

    def _read_line(self, timeout: float = 1.0) -> Optional[str]:
        deadline = time.monotonic() + timeout
        buf = b""
        while time.monotonic() < deadline:
            ch = self._ser.read(1)
            if ch:
                buf += ch
                if buf.endswith(b"\n"):
                    return buf.decode(errors="replace")
        return buf.decode(errors="replace") if buf else None

    def _at_cmd(self, cmd: str, timeout: float = 2.0) -> str:
        with self._lock:
            self._write(cmd + "\r\n")
            resp = self._read_line(timeout=timeout) or ""
            if "+ERR" in resp:
                raise RadioError(f"AT command failed: {cmd!r} → {resp.strip()}")
            return resp
