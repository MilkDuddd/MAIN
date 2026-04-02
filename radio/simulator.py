"""
UDP-based radio simulator for testing without hardware.

Each simulated node binds to  127.0.0.1:(BASE_PORT + node_id)  and
sends packets to the broadcast address 127.0.0.255 so all local nodes
receive every transmission — exactly like a shared radio channel.

Run multiple instances in separate terminals:
  NODE_ID=1 python main.py --driver sim --alias Alice
  NODE_ID=2 python main.py --driver sim --alias Bob
  NODE_ID=3 python main.py --driver sim --alias Charlie

You can also forward simulator traffic across a real network by pointing
the broadcast address at a VPN or LAN subnet broadcast address.
"""

import random
import socket
import threading
import time
import queue
from typing import Optional, Tuple

from .base import BaseRadio, RadioError


class SimulatorRadio(BaseRadio):
    """
    Simulates a shared broadcast radio channel using UDP sockets.

    Supports configurable packet loss and latency to test mesh routing.
    """

    def __init__(self, config=None, node_id: int = 1):
        from config import SimulatorConfig, NODE_ID
        self._cfg     = config or SimulatorConfig()
        self._node_id = node_id or NODE_ID
        self._sock: Optional[socket.socket] = None
        self._rx_queue: queue.Queue = queue.Queue()
        self._rx_thread: Optional[threading.Thread] = None
        self._running = False
        self._open = False

        self._tx_port  = self._cfg.base_port + self._node_id
        self._bcast_ip = self._cfg.host      # loopback broadcast

    # ── BaseRadio interface ────────────────────────────────

    def start(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.settimeout(0.5)
        self._sock.bind(("", self._tx_port))
        self._open = True

        self._running = True
        self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self._rx_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._rx_thread:
            self._rx_thread.join(timeout=2.0)
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open

    def send(self, data: bytes) -> None:
        if not self._open:
            raise RadioError("Simulator not started")

        # Simulated packet loss
        if self._cfg.packet_loss > 0 and random.random() < self._cfg.packet_loss:
            return   # packet "lost in the ether"

        # Send to all nodes by broadcasting to every expected port in range 0–99
        # (simulates 100 possible nodes on localhost)
        frame = _SimFrame.encode(self._node_id, data)

        # Broadcast to all ports in the simulator range
        for offset in range(100):
            port = self._cfg.base_port + offset
            if port == self._tx_port:
                continue   # don't send to ourselves
            try:
                self._sock.sendto(frame, (self._bcast_ip, port))
            except OSError:
                pass   # port not bound — no node there, that's fine

        # Simulate propagation latency
        if self._cfg.latency > 0:
            time.sleep(self._cfg.latency)

    def recv(self, timeout: Optional[float] = None) -> Optional[Tuple[bytes, int, float]]:
        try:
            return self._rx_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # ── Background RX thread ───────────────────────────────

    def _rx_loop(self) -> None:
        while self._running:
            try:
                raw, addr = self._sock.recvfrom(512)
                frame = _SimFrame.decode(raw)
                if frame is None:
                    continue
                sender_id, payload = frame
                if sender_id == self._node_id:
                    continue   # ignore our own echoes

                # Simulated RSSI / SNR (fake but plausible values)
                rssi = random.randint(-110, -60)
                snr  = round(random.uniform(-5.0, 12.0), 1)
                self._rx_queue.put((payload, rssi, snr))

            except socket.timeout:
                pass
            except OSError:
                if self._running:
                    raise


# ──────────────────────────────────────────────────────────
# Simple frame format for the simulator UDP packets
#   4 bytes: magic "LORA"
#   4 bytes: sender node_id (big-endian uint32)
#   N bytes: payload
# ──────────────────────────────────────────────────────────

import struct

_MAGIC = b"LORA"


class _SimFrame:
    @staticmethod
    def encode(sender_id: int, payload: bytes) -> bytes:
        return _MAGIC + struct.pack(">I", sender_id) + payload

    @staticmethod
    def decode(raw: bytes) -> Optional[Tuple[int, bytes]]:
        if len(raw) < 8 or raw[:4] != _MAGIC:
            return None
        sender_id = struct.unpack_from(">I", raw, 4)[0]
        payload   = raw[8:]
        return sender_id, payload
