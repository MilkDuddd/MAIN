"""
SX127x (SX1276 / SX1278) LoRa radio driver via SPI.

Tested with:
  - WaveShare SX1276 LoRa HAT
  - Adafruit RFM95W (SX1276)
  - Generic SX1278 breakout boards

Wiring (Raspberry Pi BCM numbering — change in SX127xConfig)
──────────────────────────────────────────────────────────────
  SX127x       RPi
  ──────────── ─────────────────────────
  VCC          3.3 V
  GND          GND
  SCK          GPIO 11 (SPI0 CLK)
  MISO         GPIO 9  (SPI0 MISO)
  MOSI         GPIO 10 (SPI0 MOSI)
  NSS / CS     GPIO 8  (SPI0 CE0)   ← spi_device=0
  RESET        GPIO 22              ← reset_pin
  DIO0         GPIO 4               ← dio0_pin

Install dependencies on the Pi:
  sudo apt install python3-spidev python3-rpi.gpio
  pip install spidev RPi.GPIO

SX1276 register map references
  https://cdn.sparkfun.com/assets/learn_tutorials/8/0/4/SX1276_77_78_79.pdf
"""

import time
import threading
import queue
from typing import Optional, Tuple

from .base import BaseRadio, RadioError

try:
    import spidev
    import RPi.GPIO as GPIO
    _HW_AVAILABLE = True
except ImportError:
    _HW_AVAILABLE = False


# ──────────────────────────────────────────────────────────
# SX127x register addresses
# ──────────────────────────────────────────────────────────

REG_FIFO                = 0x00
REG_OP_MODE             = 0x01
REG_FRF_MSB             = 0x06
REG_FRF_MID             = 0x07
REG_FRF_LSB             = 0x08
REG_PA_CONFIG           = 0x09
REG_LNA                 = 0x0C
REG_FIFO_ADDR_PTR       = 0x0D
REG_FIFO_TX_BASE_ADDR   = 0x0E
REG_FIFO_RX_BASE_ADDR   = 0x0F
REG_FIFO_RX_CURRENT_ADDR = 0x10
REG_IRQ_FLAGS_MASK      = 0x11
REG_IRQ_FLAGS           = 0x12
REG_RX_NB_BYTES         = 0x13
REG_PKT_SNR_VALUE       = 0x19
REG_PKT_RSSI_VALUE      = 0x1A
REG_MODEM_CONFIG_1      = 0x1D
REG_MODEM_CONFIG_2      = 0x1E
REG_PREAMBLE_MSB        = 0x20
REG_PREAMBLE_LSB        = 0x21
REG_PAYLOAD_LENGTH      = 0x22
REG_MODEM_CONFIG_3      = 0x26
REG_FREQ_ERROR_MSB      = 0x28
REG_RSSI_WIDEBAND       = 0x2C
REG_DETECTION_OPTIMIZE  = 0x31
REG_INVERTIQ            = 0x33
REG_DETECTION_THRESHOLD = 0x37
REG_SYNC_WORD           = 0x39
REG_INVERTIQ2           = 0x3B
REG_DIO_MAPPING_1       = 0x40
REG_VERSION             = 0x42
REG_PA_DAC              = 0x4D

# Operating modes
MODE_LONG_RANGE   = 0x80
MODE_SLEEP        = 0x00
MODE_STDBY        = 0x01
MODE_TX           = 0x03
MODE_RX_CONT      = 0x05
MODE_RX_SINGLE    = 0x06

# IRQ flags
IRQ_TX_DONE       = 0x08
IRQ_PAYLOAD_CRC_ERROR = 0x20
IRQ_RX_DONE       = 0x40

# PA config
PA_BOOST          = 0x80

# Expected chip version
CHIP_VERSION      = 0x12

# SYNC word: 0x12 = LoRa private network (0x34 = LoRaWAN)
LORA_SYNC_WORD    = 0x12

FXOSC = 32_000_000.0   # SX127x crystal frequency


# ──────────────────────────────────────────────────────────
# Driver
# ──────────────────────────────────────────────────────────

class SX127xRadio(BaseRadio):
    """
    Full-duplex LoRa driver using direct SPI register access.

    A background thread continuously listens for incoming packets
    and queues them; the main thread can call recv() at any time.
    """

    def __init__(self, config=None):
        from config import SX127xConfig
        self._cfg = config or SX127xConfig()
        self._spi: Optional[object] = None
        self._rx_queue: queue.Queue = queue.Queue()
        self._rx_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._open = False

    # ── BaseRadio interface ────────────────────────────────

    def start(self) -> None:
        if not _HW_AVAILABLE:
            raise RadioError(
                "spidev / RPi.GPIO not available. "
                "Install them on a Raspberry Pi or use the simulator driver."
            )
        self._init_spi()
        self._init_gpio()
        self._reset()
        self._check_version()
        self._configure()
        self._open = True

        # Start background RX thread
        self._running = True
        self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self._rx_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._rx_thread:
            self._rx_thread.join(timeout=3.0)
        if self._spi:
            self._spi.close()
        if _HW_AVAILABLE:
            GPIO.cleanup()
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    def send(self, data: bytes) -> None:
        if len(data) > 255:
            raise RadioError(f"Payload too long: {len(data)} bytes (max 255)")
        with self._lock:
            # Switch to standby
            self._write_reg(REG_OP_MODE, MODE_LONG_RANGE | MODE_STDBY)
            time.sleep(0.01)

            # Map DIO0 to TxDone
            self._write_reg(REG_DIO_MAPPING_1, 0x40)

            # Reset FIFO ptr, write payload
            self._write_reg(REG_FIFO_ADDR_PTR, self._read_reg(REG_FIFO_TX_BASE_ADDR))
            self._write_reg(REG_PAYLOAD_LENGTH, len(data))
            self._write_fifo(data)

            # Clear TX IRQ flags and start TX
            self._write_reg(REG_IRQ_FLAGS, IRQ_TX_DONE)
            self._write_reg(REG_OP_MODE, MODE_LONG_RANGE | MODE_TX)

            # Wait for TxDone (poll DIO0 or IRQ flag)
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                irq = self._read_reg(REG_IRQ_FLAGS)
                if irq & IRQ_TX_DONE:
                    break
                time.sleep(0.01)
            else:
                raise RadioError("TX timeout: TxDone never asserted")

            self._write_reg(REG_IRQ_FLAGS, IRQ_TX_DONE)
            # Return to continuous RX
            self._write_reg(REG_OP_MODE, MODE_LONG_RANGE | MODE_RX_CONT)

    def recv(self, timeout: Optional[float] = None) -> Optional[Tuple[bytes, int, float]]:
        try:
            return self._rx_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # ── Hardware init ──────────────────────────────────────

    def _init_spi(self) -> None:
        self._spi = spidev.SpiDev()
        self._spi.open(self._cfg.spi_bus, self._cfg.spi_device)
        self._spi.max_speed_hz = self._cfg.spi_speed_hz
        self._spi.mode = 0b00

    def _init_gpio(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._cfg.reset_pin, GPIO.OUT)
        GPIO.setup(self._cfg.dio0_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def _reset(self) -> None:
        GPIO.output(self._cfg.reset_pin, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self._cfg.reset_pin, GPIO.HIGH)
        time.sleep(0.01)

    def _check_version(self) -> None:
        version = self._read_reg(REG_VERSION)
        if version != CHIP_VERSION:
            raise RadioError(
                f"Unexpected SX127x version: 0x{version:02X} (expected 0x{CHIP_VERSION:02X}). "
                "Check wiring."
            )

    def _configure(self) -> None:
        cfg = self._cfg

        # Sleep mode, LoRa
        self._write_reg(REG_OP_MODE, MODE_LONG_RANGE | MODE_SLEEP)
        time.sleep(0.01)

        # Frequency
        frf = int((cfg.frequency / FXOSC) * (1 << 19))
        self._write_reg(REG_FRF_MSB, (frf >> 16) & 0xFF)
        self._write_reg(REG_FRF_MID, (frf >>  8) & 0xFF)
        self._write_reg(REG_FRF_LSB,  frf        & 0xFF)

        # TX power via PA_BOOST
        if cfg.tx_power > 17:
            self._write_reg(REG_PA_DAC, 0x87)
            self._write_reg(REG_PA_CONFIG, PA_BOOST | (cfg.tx_power - 5))
        else:
            self._write_reg(REG_PA_DAC, 0x84)
            self._write_reg(REG_PA_CONFIG, PA_BOOST | (cfg.tx_power - 2))

        # LNA gain = max, AGC on
        self._write_reg(REG_LNA, 0x23)

        # Modem config 1: BW + CR + implicit header off
        bw_map = {7800: 0, 10400: 1, 15600: 2, 20800: 3, 31250: 4,
                  41700: 5, 62500: 6, 125000: 7, 250000: 8, 500000: 9}
        bw_bits = bw_map.get(cfg.bandwidth, 7) << 4
        cr_bits = (cfg.coding_rate - 4) << 1
        self._write_reg(REG_MODEM_CONFIG_1, bw_bits | cr_bits | 0x00)

        # Modem config 2: SF + TX cont off + CRC on/off + RX timeout MSB
        crc_bit = 0x04 if cfg.crc_enabled else 0x00
        self._write_reg(REG_MODEM_CONFIG_2, (cfg.spreading_factor << 4) | crc_bit | 0x03)

        # Modem config 3: Low data rate opt on for SF11/12
        ldr = 0x08 if cfg.spreading_factor >= 11 else 0x00
        self._write_reg(REG_MODEM_CONFIG_3, ldr | 0x04)  # AGC auto on

        # SF6 special case
        if cfg.spreading_factor == 6:
            self._write_reg(REG_DETECTION_OPTIMIZE, 0xC5)
            self._write_reg(REG_DETECTION_THRESHOLD, 0x0C)
        else:
            self._write_reg(REG_DETECTION_OPTIMIZE, 0xC3)
            self._write_reg(REG_DETECTION_THRESHOLD, 0x0A)

        # Preamble
        self._write_reg(REG_PREAMBLE_MSB, (cfg.preamble_length >> 8) & 0xFF)
        self._write_reg(REG_PREAMBLE_LSB,  cfg.preamble_length        & 0xFF)

        # Sync word (0x12 = private, 0x34 = LoRaWAN)
        self._write_reg(REG_SYNC_WORD, LORA_SYNC_WORD)

        # FIFO base addresses
        self._write_reg(REG_FIFO_TX_BASE_ADDR, 0x00)
        self._write_reg(REG_FIFO_RX_BASE_ADDR, 0x00)

        # Map DIO0 to RxDone
        self._write_reg(REG_DIO_MAPPING_1, 0x00)

        # Standby then continuous RX
        self._write_reg(REG_OP_MODE, MODE_LONG_RANGE | MODE_STDBY)
        time.sleep(0.01)
        self._write_reg(REG_OP_MODE, MODE_LONG_RANGE | MODE_RX_CONT)

    # ── Background RX thread ───────────────────────────────

    def _rx_loop(self) -> None:
        while self._running:
            irq = self._read_reg(REG_IRQ_FLAGS)
            if irq & IRQ_RX_DONE:
                self._handle_rx(irq)
            time.sleep(0.005)

    def _handle_rx(self, irq: int) -> None:
        with self._lock:
            # Always clear all IRQ flags first
            self._write_reg(REG_IRQ_FLAGS, 0xFF)

            if irq & IRQ_PAYLOAD_CRC_ERROR:
                return   # Drop bad packet

            nb_bytes = self._read_reg(REG_RX_NB_BYTES)
            rx_addr  = self._read_reg(REG_FIFO_RX_CURRENT_ADDR)
            self._write_reg(REG_FIFO_ADDR_PTR, rx_addr)
            data = bytes(self._spi.readbytes(nb_bytes))

            # RSSI / SNR
            snr_raw  = self._read_reg(REG_PKT_SNR_VALUE)
            snr      = (snr_raw if snr_raw < 128 else snr_raw - 256) / 4.0
            rssi_raw = self._read_reg(REG_PKT_RSSI_VALUE)
            rssi     = rssi_raw - (164 if self._cfg.frequency < 700e6 else 157)

        if data:
            self._rx_queue.put((data, rssi, snr))

    # ── SPI helpers ────────────────────────────────────────

    def _read_reg(self, addr: int) -> int:
        return self._spi.xfer2([addr & 0x7F, 0x00])[1]

    def _write_reg(self, addr: int, value: int) -> None:
        self._spi.xfer2([addr | 0x80, value & 0xFF])

    def _write_fifo(self, data: bytes) -> None:
        self._spi.xfer2([REG_FIFO | 0x80] + list(data))
