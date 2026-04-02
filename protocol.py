"""
Wire protocol for the encrypted LoRa mesh network.

Packet layout (all fields big-endian)
──────────────────────────────────────
Byte  0      : version   (uint8)  — currently 0x01
Byte  1      : type      (uint8)  — MessageType enum
Bytes 2–5    : src_id    (uint32) — sender node ID
Bytes 6–9    : dst_id    (uint32) — destination (0xFFFFFFFF = broadcast)
Byte  10     : ttl       (uint8)  — hop limit; decremented each hop
Bytes 11–12  : seq       (uint16) — per-source sequence number (wraps)
Bytes 13–14  : flags     (uint16) — bitmask (see Flags)
Bytes 15–16  : payload_len (uint16)
Bytes 17+    : payload

Total header = 17 bytes.
Maximum LoRa payload = 255 bytes → max encrypted payload = 238 bytes.

Fragmentation
─────────────
If a plaintext message exceeds MAX_PAYLOAD bytes after encryption overhead,
it is split into fragments.  Fragment flag bits encode frag_index and
frag_total in the flags field (see Flags below).

Payload contents per MessageType
─────────────────────────────────
DATA          : encrypted ciphertext (nonce 12B || ciphertext || tag 16B)
KEY_EXCHANGE  : raw X25519 public key (32 bytes) — plaintext, not encrypted
ACK           : 2-byte seq number being acknowledged
PING          : 4-byte sender timestamp (millis, uint32)
PONG          : 4-byte echoed timestamp
ANNOUNCE      : alias (UTF-8, up to 32 bytes)
"""

import struct
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterator, List, Optional

PROTOCOL_VERSION = 0x01
HEADER_LEN       = 17
MAX_LORA_PAYLOAD = 255     # SX127x max
MAX_PAYLOAD      = MAX_LORA_PAYLOAD - HEADER_LEN   # 238 bytes


class MessageType(IntEnum):
    DATA         = 0x01
    KEY_EXCHANGE = 0x02
    ACK          = 0x03
    PING         = 0x04
    PONG         = 0x05
    ANNOUNCE     = 0x06


class Flags(IntEnum):
    NONE        = 0x0000
    WANTS_ACK   = 0x0001   # sender requests an ACK
    FRAGMENTED  = 0x0002   # this is a fragment
    # bits 2–4: frag_index (0-based, 3 bits → up to 8 fragments)
    # bits 5–7: frag_total  (3 bits → 1–8 total)
    # bit  8:   reserved
    ENCRYPTED   = 0x0100   # payload is encrypted (DATA messages always are)


FRAG_INDEX_SHIFT = 2
FRAG_INDEX_MASK  = 0x7   # 3 bits
FRAG_TOTAL_SHIFT = 5
FRAG_TOTAL_MASK  = 0x7   # 3 bits


# ──────────────────────────────────────────────────────────
# Packet dataclass
# ──────────────────────────────────────────────────────────

@dataclass
class Packet:
    version:     int         = PROTOCOL_VERSION
    type:        MessageType = MessageType.DATA
    src_id:      int         = 0
    dst_id:      int         = 0xFFFFFFFF
    ttl:         int         = 7
    seq:         int         = 0
    flags:       int         = 0
    payload:     bytes       = b""

    # Not serialised — populated when received
    rssi: Optional[int] = field(default=None, repr=False)
    snr:  Optional[float] = field(default=None, repr=False)

    # ── Flag helpers ───────────────────────────────────────

    def set_flag(self, flag: Flags) -> None:
        self.flags |= int(flag)

    def has_flag(self, flag: Flags) -> bool:
        return bool(self.flags & int(flag))

    def set_fragment(self, index: int, total: int) -> None:
        self.set_flag(Flags.FRAGMENTED)
        self.flags &= ~(FRAG_INDEX_MASK << FRAG_INDEX_SHIFT)
        self.flags &= ~(FRAG_TOTAL_MASK << FRAG_TOTAL_SHIFT)
        self.flags |= (index & FRAG_INDEX_MASK) << FRAG_INDEX_SHIFT
        self.flags |= ((total - 1) & FRAG_TOTAL_MASK) << FRAG_TOTAL_SHIFT

    @property
    def frag_index(self) -> int:
        return (self.flags >> FRAG_INDEX_SHIFT) & FRAG_INDEX_MASK

    @property
    def frag_total(self) -> int:
        return ((self.flags >> FRAG_TOTAL_SHIFT) & FRAG_TOTAL_MASK) + 1

    # ── (De)serialisation ──────────────────────────────────

    def to_bytes(self) -> bytes:
        # Header layout (17 bytes):
        #  B  version
        #  B  type
        #  I  src_id   (4 B, big-endian)
        #  I  dst_id   (4 B)
        #  B  ttl
        #  H  seq      (2 B)
        #  H  flags    (2 B)
        #  H  payload_len (2 B)
        header = struct.pack(
            ">BBIIBHHH",
            self.version,
            int(self.type),
            self.src_id,
            self.dst_id,
            self.ttl,
            self.seq,
            self.flags,
            len(self.payload),
        )
        return header + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> "Packet":
        if len(data) < HEADER_LEN:
            raise ValueError(f"Packet too short: {len(data)} bytes (need {HEADER_LEN})")
        version, ptype, src_id, dst_id, ttl, seq, flags, plen = struct.unpack_from(
            ">BBIIBHHH", data, 0
        )
        payload = data[HEADER_LEN : HEADER_LEN + plen]
        return cls(
            version=version,
            type=MessageType(ptype),
            src_id=src_id,
            dst_id=dst_id,
            ttl=ttl,
            seq=seq,
            flags=flags,
            payload=payload,
        )

    @property
    def header_bytes(self) -> bytes:
        """Return just the header bytes (used as AAD for encryption)."""
        return self.to_bytes()[:HEADER_LEN]

    @property
    def message_id(self) -> tuple:
        """Unique message identifier for dedup cache: (src_id, seq)."""
        return (self.src_id, self.seq)

    def is_broadcast(self) -> bool:
        return self.dst_id == 0xFFFFFFFF


# ──────────────────────────────────────────────────────────
# Packet builder helpers
# ──────────────────────────────────────────────────────────

class PacketBuilder:
    """
    Stateful builder that tracks per-source sequence numbers.
    One instance per local node.
    """

    def __init__(self, src_id: int, default_ttl: int = 7):
        self._src_id = src_id
        self._default_ttl = default_ttl
        self._seq: int = 0

    def _next_seq(self) -> int:
        s = self._seq
        self._seq = (self._seq + 1) & 0xFFFF
        return s

    def data(
        self,
        payload: bytes,
        dst_id: int = 0xFFFFFFFF,
        wants_ack: bool = False,
        ttl: Optional[int] = None,
    ) -> "Packet":
        pkt = Packet(
            type=MessageType.DATA,
            src_id=self._src_id,
            dst_id=dst_id,
            ttl=ttl if ttl is not None else self._default_ttl,
            seq=self._next_seq(),
            flags=Flags.ENCRYPTED,
            payload=payload,
        )
        if wants_ack:
            pkt.set_flag(Flags.WANTS_ACK)
        return pkt

    def key_exchange(self, public_bytes: bytes, dst_id: int = 0xFFFFFFFF) -> "Packet":
        return Packet(
            type=MessageType.KEY_EXCHANGE,
            src_id=self._src_id,
            dst_id=dst_id,
            ttl=self._default_ttl,
            seq=self._next_seq(),
            flags=Flags.NONE,
            payload=public_bytes,
        )

    def ack(self, ack_seq: int, dst_id: int) -> "Packet":
        return Packet(
            type=MessageType.ACK,
            src_id=self._src_id,
            dst_id=dst_id,
            ttl=1,              # ACKs don't need to flood the mesh
            seq=self._next_seq(),
            flags=Flags.NONE,
            payload=struct.pack(">H", ack_seq),
        )

    def ping(self, dst_id: int = 0xFFFFFFFF) -> "Packet":
        ts = int(time.monotonic() * 1000) & 0xFFFFFFFF
        return Packet(
            type=MessageType.PING,
            src_id=self._src_id,
            dst_id=dst_id,
            ttl=self._default_ttl,
            seq=self._next_seq(),
            payload=struct.pack(">I", ts),
        )

    def pong(self, ping_pkt: "Packet") -> "Packet":
        return Packet(
            type=MessageType.PONG,
            src_id=self._src_id,
            dst_id=ping_pkt.src_id,
            ttl=self._default_ttl,
            seq=self._next_seq(),
            payload=ping_pkt.payload,   # echo back the timestamp
        )

    def announce(self, alias: str) -> "Packet":
        return Packet(
            type=MessageType.ANNOUNCE,
            src_id=self._src_id,
            dst_id=0xFFFFFFFF,
            ttl=self._default_ttl,
            seq=self._next_seq(),
            payload=alias.encode()[:32],
        )


# ──────────────────────────────────────────────────────────
# Fragmentation / reassembly
# ──────────────────────────────────────────────────────────

def fragment_payload(
    builder: PacketBuilder,
    payload: bytes,
    dst_id: int = 0xFFFFFFFF,
    wants_ack: bool = False,
    ttl: Optional[int] = None,
) -> List["Packet"]:
    """
    Split a large payload into multiple DATA packets that each fit within
    MAX_PAYLOAD bytes.  Max 8 fragments supported.
    """
    chunks = [payload[i : i + MAX_PAYLOAD] for i in range(0, len(payload), MAX_PAYLOAD)]
    if len(chunks) > 8:
        raise ValueError(f"Payload too large: would need {len(chunks)} fragments (max 8)")
    if len(chunks) == 1:
        return [builder.data(payload, dst_id=dst_id, wants_ack=wants_ack, ttl=ttl)]

    packets = []
    for i, chunk in enumerate(chunks):
        pkt = builder.data(chunk, dst_id=dst_id, wants_ack=(wants_ack and i == len(chunks) - 1), ttl=ttl)
        pkt.set_fragment(i, len(chunks))
        packets.append(pkt)
    return packets


class FragmentReassembler:
    """
    Reassembles fragmented messages.
    Keyed by (src_id, base_seq_of_first_fragment).
    """

    def __init__(self, timeout: float = 30.0):
        self._timeout = timeout
        # key -> (timestamp, total, {index: bytes})
        self._buffers: dict = {}

    def add(self, pkt: "Packet") -> Optional[bytes]:
        """
        Add a fragment.  Returns the reassembled payload when all fragments
        are present, or None if still waiting.
        """
        if not pkt.has_flag(Flags.FRAGMENTED):
            return pkt.payload

        key = (pkt.src_id, pkt.seq - pkt.frag_index)  # approximate base seq
        now = time.monotonic()

        # Purge stale buffers
        stale = [k for k, v in self._buffers.items() if now - v[0] > self._timeout]
        for k in stale:
            del self._buffers[k]

        if key not in self._buffers:
            self._buffers[key] = (now, pkt.frag_total, {})

        _, total, frags = self._buffers[key]
        frags[pkt.frag_index] = pkt.payload

        if len(frags) == total:
            del self._buffers[key]
            return b"".join(frags[i] for i in range(total))

        return None
