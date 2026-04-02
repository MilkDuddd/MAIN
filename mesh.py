"""
Mesh networking layer.

Responsibilities
────────────────
1. Receive raw bytes from the radio, parse them into Packets.
2. Decrypt DATA payloads using the KeyStore.
3. Deliver messages addressed to this node (or broadcast) to the application.
4. Re-broadcast messages destined for other nodes (relay mode), decrementing TTL.
5. Deduplicate packets (seen-message cache by (src_id, seq)).
6. Handle KEY_EXCHANGE handshakes automatically.
7. Handle PING/PONG, ANNOUNCE internally.
8. Retransmit outgoing messages until ACK received (when WANTS_ACK is set).

The application interacts with MeshNode via:
  node.send_message(text, dst_id=BROADCAST_ID)
  msg = node.recv_message(timeout=2.0)   # returns Message namedtuple or None

All radio I/O runs on a background thread. The application thread only
calls send_message / recv_message.
"""

import time
import threading
import queue
import logging
from dataclasses import dataclass
from typing import Optional, Callable

from cryptography.exceptions import InvalidTag

from config import BROADCAST_ID, MeshConfig, NODE_ID, NODE_ALIAS, KEYS_DIR
from crypto import KeyStore, NodeKeypair, encrypt, decrypt
from protocol import (
    Packet, PacketBuilder, MessageType, Flags,
    fragment_payload, FragmentReassembler,
    MAX_PAYLOAD, HEADER_LEN,
)
from radio.base import BaseRadio

log = logging.getLogger("mesh")


# ──────────────────────────────────────────────────────────
# Public types
# ──────────────────────────────────────────────────────────

@dataclass
class Message:
    """A decrypted, reassembled message delivered to the application."""
    src_id:   int
    dst_id:   int
    text:     str
    alias:    str          # sender's human-readable alias (if known)
    rssi:     Optional[int]  = None
    snr:      Optional[float] = None
    timestamp: float         = 0.0


@dataclass
class PeerInfo:
    node_id: int
    alias:   str = ""
    rssi:    Optional[int]  = None
    snr:     Optional[float] = None
    last_seen: float = 0.0


# ──────────────────────────────────────────────────────────
# Mesh node
# ──────────────────────────────────────────────────────────

class MeshNode:
    """
    High-level mesh networking node.

    Usage:
      node = MeshNode(radio, keystore, node_id=1, alias="Alice")
      node.start()
      node.send_message("Hello!")
      msg = node.recv_message(timeout=5.0)
      node.stop()
    """

    def __init__(
        self,
        radio: BaseRadio,
        keystore: KeyStore,
        keypair: Optional[NodeKeypair] = None,
        node_id:  int = NODE_ID,
        alias:    str = NODE_ALIAS,
        config:   MeshConfig = None,
        on_message: Optional[Callable[[Message], None]] = None,
    ):
        self._radio    = radio
        self._keystore = keystore
        self._keypair  = keypair
        self._node_id  = node_id
        self._alias    = alias
        self._cfg      = config or MeshConfig()
        self._on_message = on_message

        self._builder    = PacketBuilder(node_id, default_ttl=self._cfg.max_ttl)
        self._reassembler = FragmentReassembler()

        # Queues
        self._msg_queue: queue.Queue  = queue.Queue()
        self._tx_queue:  queue.Queue  = queue.Queue()

        # State
        self._seen:  dict = {}        # (src_id, seq) → expire_time
        self._peers: dict = {}        # node_id → PeerInfo
        self._pending_acks: dict = {} # seq → (packet, attempts, next_retry)
        self._lock = threading.Lock()

        self._running = False
        self._rx_thread: Optional[threading.Thread] = None
        self._tx_thread: Optional[threading.Thread] = None
        self._retry_thread: Optional[threading.Thread] = None

    # ── Lifecycle ──────────────────────────────────────────

    def start(self) -> None:
        self._running = True
        self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True, name="mesh-rx")
        self._tx_thread = threading.Thread(target=self._tx_loop, daemon=True, name="mesh-tx")
        self._retry_thread = threading.Thread(target=self._retry_loop, daemon=True, name="mesh-retry")
        self._rx_thread.start()
        self._tx_thread.start()
        self._retry_thread.start()

        # Announce ourselves
        self._enqueue_tx(self._builder.announce(self._alias))
        # Broadcast our public key if we have one
        if self._keypair:
            self._enqueue_tx(self._builder.key_exchange(self._keypair.public_bytes))

    def stop(self) -> None:
        self._running = False
        # Unblock blocking queues
        self._tx_queue.put(None)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    # ── Public API ─────────────────────────────────────────

    def send_message(
        self,
        text: str,
        dst_id: int = BROADCAST_ID,
        wants_ack: bool = False,
    ) -> None:
        """Encrypt and send a text message."""
        plaintext = text.encode("utf-8")
        key = self._keystore.get_key(dst_id if dst_id != BROADCAST_ID else BROADCAST_ID)

        if key is None:
            # No key yet — initiate key exchange and queue message
            if self._keypair and dst_id != BROADCAST_ID:
                self._enqueue_tx(self._builder.key_exchange(self._keypair.public_bytes, dst_id=dst_id))
            raise RuntimeError(
                f"No encryption key for node {dst_id:#010x}. "
                "Key exchange in progress — try again in a moment."
            )

        # Fragment if needed
        # Estimate ciphertext size: plaintext + 12 (nonce) + 16 (tag)
        est_cipher_len = len(plaintext) + 12 + 16
        if est_cipher_len > MAX_PAYLOAD:
            # Encrypt each fragment separately
            chunks = [plaintext[i : i + (MAX_PAYLOAD - 28)] for i in range(0, len(plaintext), MAX_PAYLOAD - 28)]
            for i, chunk in enumerate(chunks):
                dummy_pkt = self._builder.data(b"", dst_id=dst_id)
                ciphertext = encrypt(key, chunk, aad=dummy_pkt.header_bytes)
                pkt = self._builder.data(ciphertext, dst_id=dst_id, wants_ack=(wants_ack and i == len(chunks) - 1))
                if len(chunks) > 1:
                    pkt.set_fragment(i, len(chunks))
                self._enqueue_tx(pkt)
        else:
            dummy_pkt = self._builder.data(b"", dst_id=dst_id)
            ciphertext = encrypt(key, plaintext, aad=dummy_pkt.header_bytes)
            pkt = self._builder.data(ciphertext, dst_id=dst_id, wants_ack=wants_ack)
            if wants_ack:
                with self._lock:
                    self._pending_acks[pkt.seq] = (pkt, 0, time.monotonic())
            self._enqueue_tx(pkt)

    def recv_message(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Block until a message arrives or timeout expires."""
        try:
            return self._msg_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def ping(self, dst_id: int = BROADCAST_ID) -> None:
        self._enqueue_tx(self._builder.ping(dst_id))

    def peers(self) -> list:
        with self._lock:
            return list(self._peers.values())

    # ── TX path ────────────────────────────────────────────

    def _enqueue_tx(self, pkt: Packet) -> None:
        self._tx_queue.put(pkt)

    def _tx_loop(self) -> None:
        while self._running:
            try:
                pkt = self._tx_queue.get(timeout=0.5)
                if pkt is None:
                    break
                raw = pkt.to_bytes()
                try:
                    self._radio.send(raw)
                except Exception as e:
                    log.error("TX error: %s", e)
            except queue.Empty:
                pass

    # ── RX path ────────────────────────────────────────────

    def _rx_loop(self) -> None:
        while self._running:
            try:
                result = self._radio.recv(timeout=0.5)
                if result is None:
                    continue
                raw, rssi, snr = result
                self._handle_raw(raw, rssi, snr)
            except Exception as e:
                log.error("RX error: %s", e)

    def _handle_raw(self, raw: bytes, rssi: int, snr: float) -> None:
        try:
            pkt = Packet.from_bytes(raw)
        except Exception as e:
            log.debug("Bad packet: %s", e)
            return

        pkt.rssi = rssi
        pkt.snr  = snr

        # Dedup
        msg_id = pkt.message_id
        now = time.monotonic()
        with self._lock:
            if msg_id in self._seen:
                return   # already processed
            self._seen[msg_id] = now + self._cfg.dedup_ttl
            # Prune expired entries
            expired = [k for k, v in self._seen.items() if v < now]
            for k in expired:
                del self._seen[k]

        # Update peer info
        self._update_peer(pkt.src_id, rssi, snr)

        # Is this packet for us (or broadcast)?
        for_us = pkt.dst_id in (self._node_id, BROADCAST_ID)

        if for_us:
            self._dispatch(pkt)

        # Relay if TTL allows and relay mode is on
        if self._cfg.relay and pkt.ttl > 1 and not for_us:
            pkt.ttl -= 1
            self._enqueue_tx(pkt)

    def _dispatch(self, pkt: Packet) -> None:
        t = pkt.type

        if t == MessageType.DATA:
            self._handle_data(pkt)
        elif t == MessageType.KEY_EXCHANGE:
            self._handle_key_exchange(pkt)
        elif t == MessageType.ACK:
            self._handle_ack(pkt)
        elif t == MessageType.PING:
            self._enqueue_tx(self._builder.pong(pkt))
        elif t == MessageType.PONG:
            self._handle_pong(pkt)
        elif t == MessageType.ANNOUNCE:
            self._handle_announce(pkt)

    def _handle_data(self, pkt: Packet) -> None:
        key = self._keystore.get_key(pkt.src_id)
        if key is None:
            log.warning("No key for src %#010x — requesting key exchange", pkt.src_id)
            if self._keypair:
                self._enqueue_tx(self._builder.key_exchange(self._keypair.public_bytes, dst_id=pkt.src_id))
            return

        try:
            plaintext = decrypt(key, pkt.payload, aad=pkt.header_bytes)
        except InvalidTag:
            log.warning("Auth tag mismatch from %#010x seq=%d (wrong key?)", pkt.src_id, pkt.seq)
            return
        except Exception as e:
            log.warning("Decrypt error from %#010x: %s", pkt.src_id, e)
            return

        # Reassemble fragments if needed
        assembled = self._reassembler.add(
            _PayloadPatch(pkt, plaintext)
        )
        if assembled is None:
            return   # waiting for more fragments

        # Send ACK if requested
        if pkt.has_flag(Flags.WANTS_ACK):
            self._enqueue_tx(self._builder.ack(pkt.seq, dst_id=pkt.src_id))

        peer = self._peers.get(pkt.src_id)
        alias = peer.alias if peer else f"node-{pkt.src_id}"

        msg = Message(
            src_id=pkt.src_id,
            dst_id=pkt.dst_id,
            text=assembled.decode("utf-8", errors="replace"),
            alias=alias,
            rssi=pkt.rssi,
            snr=pkt.snr,
            timestamp=time.time(),
        )
        self._msg_queue.put(msg)
        if self._on_message:
            self._on_message(msg)

    def _handle_key_exchange(self, pkt: Packet) -> None:
        if len(pkt.payload) != 32:
            return
        if not self._keypair:
            return

        shared_secret = self._keypair.exchange(pkt.payload)
        key = self._keystore.register_session(pkt.src_id, shared_secret, self._node_id)
        log.info("Key exchange complete with node %#010x", pkt.src_id)

        # If this was a request (broadcast), respond with our own public key
        if pkt.dst_id == BROADCAST_ID:
            self._enqueue_tx(self._builder.key_exchange(self._keypair.public_bytes, dst_id=pkt.src_id))

    def _handle_ack(self, pkt: Packet) -> None:
        import struct
        if len(pkt.payload) >= 2:
            ack_seq = struct.unpack_from(">H", pkt.payload)[0]
            with self._lock:
                self._pending_acks.pop(ack_seq, None)
            log.debug("ACK received for seq %d from %#010x", ack_seq, pkt.src_id)

    def _handle_pong(self, pkt: Packet) -> None:
        import struct
        if len(pkt.payload) >= 4:
            sent_ms = struct.unpack_from(">I", pkt.payload)[0]
            now_ms  = int(time.monotonic() * 1000) & 0xFFFFFFFF
            rtt_ms  = (now_ms - sent_ms) & 0xFFFFFFFF
            log.info("PONG from %#010x: RTT=%d ms  RSSI=%s SNR=%s",
                     pkt.src_id, rtt_ms, pkt.rssi, pkt.snr)

    def _handle_announce(self, pkt: Packet) -> None:
        alias = pkt.payload.decode("utf-8", errors="replace").strip()
        with self._lock:
            if pkt.src_id not in self._peers:
                self._peers[pkt.src_id] = PeerInfo(node_id=pkt.src_id)
            self._peers[pkt.src_id].alias = alias
        log.info("Node %#010x announced as %r", pkt.src_id, alias)

    # ── Retry loop ─────────────────────────────────────────

    def _retry_loop(self) -> None:
        while self._running:
            now = time.monotonic()
            with self._lock:
                to_remove = []
                for seq, (pkt, attempts, next_retry) in self._pending_acks.items():
                    if now < next_retry:
                        continue
                    if attempts >= self._cfg.max_retries:
                        log.warning("Message seq=%d unacked after %d retries", seq, attempts)
                        to_remove.append(seq)
                    else:
                        log.debug("Retransmit seq=%d attempt=%d", seq, attempts + 1)
                        self._tx_queue.put(pkt)
                        self._pending_acks[seq] = (
                            pkt, attempts + 1, now + self._cfg.retry_delay
                        )
                for s in to_remove:
                    del self._pending_acks[s]
            time.sleep(0.5)

    # ── Peer tracking ──────────────────────────────────────

    def _update_peer(self, node_id: int, rssi: int, snr: float) -> None:
        with self._lock:
            if node_id not in self._peers:
                self._peers[node_id] = PeerInfo(node_id=node_id)
            p = self._peers[node_id]
            p.rssi      = rssi
            p.snr       = snr
            p.last_seen = time.time()


# ──────────────────────────────────────────────────────────
# Internal helper: duck-type Packet with replaced payload
# (so FragmentReassembler's .payload access works on decrypted bytes)
# ──────────────────────────────────────────────────────────

class _PayloadPatch:
    """Wraps a Packet but substitutes the payload with decrypted bytes."""
    def __init__(self, pkt: Packet, decrypted: bytes):
        self._pkt     = pkt
        self.payload  = decrypted
        self.flags    = pkt.flags
        self.src_id   = pkt.src_id
        self.seq      = pkt.seq

    @property
    def frag_index(self):  return self._pkt.frag_index
    @property
    def frag_total(self):  return self._pkt.frag_total

    def has_flag(self, flag):
        return self._pkt.has_flag(flag)
