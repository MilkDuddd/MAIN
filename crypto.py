"""
Cryptographic layer for encrypted LoRa radio communication.

Key exchange:  X25519 ECDH
Symmetric enc: ChaCha20-Poly1305 (AEAD — authenticated encryption)
KDF:           HKDF-SHA256

Two modes
---------
1. Pre-Shared Key (PSK)
   All nodes on the network share a 32-byte key loaded from a file or
   environment variable.  Simple to set up; no handshake required.

2. Session key via X25519 ECDH
   Each node has a long-term X25519 keypair.  When two nodes first
   communicate they exchange public keys over the air (KEY_EXCHANGE
   message type).  A shared secret is derived with HKDF.

Message wire format (after outer LoRa/protocol framing strips its header)
-------------------------------------------------------------------------
  nonce (12 bytes)  ||  ciphertext+tag (variable)

The ChaCha20-Poly1305 tag (16 bytes) is appended to the ciphertext
automatically by the library.

Additional authenticated data (AAD) = the 15-byte protocol header so that
routing metadata cannot be forged without breaking the auth tag.
"""

import os
import json
import struct
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization

NONCE_LEN = 12        # ChaCha20-Poly1305 nonce length
TAG_LEN   = 16        # Poly1305 authentication tag length
KEY_LEN   = 32        # 256-bit symmetric key


# ──────────────────────────────────────────────────────────
# Keypair management
# ──────────────────────────────────────────────────────────

class NodeKeypair:
    """Long-term X25519 identity keypair for a node."""

    def __init__(self, private_key: X25519PrivateKey):
        self._private = private_key
        self._public  = private_key.public_key()

    @classmethod
    def generate(cls) -> "NodeKeypair":
        return cls(X25519PrivateKey.generate())

    @classmethod
    def load(cls, path: str) -> "NodeKeypair":
        """Load from PEM file (private key only)."""
        data = Path(path).read_bytes()
        priv = X25519PrivateKey.from_private_bytes(
            serialization.load_pem_private_key(data, password=None)
            .private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        return cls(priv)

    def save(self, path: str) -> None:
        """Save private key as PEM (chmod 600 recommended)."""
        pem = self._private.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(pem)
        p.chmod(0o600)

    @property
    def public_bytes(self) -> bytes:
        return self._public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def exchange(self, peer_public_bytes: bytes) -> bytes:
        """Perform ECDH and return the raw shared secret (32 bytes)."""
        peer_pub = X25519PublicKey.from_public_bytes(peer_public_bytes)
        return self._private.exchange(peer_pub)


# ──────────────────────────────────────────────────────────
# Key derivation
# ──────────────────────────────────────────────────────────

def derive_session_key(
    shared_secret: bytes,
    local_id: int,
    peer_id: int,
    info: bytes = b"lora-session-key-v1",
) -> bytes:
    """
    HKDF-SHA256 over the X25519 shared secret.
    Salt encodes the two node IDs so different pairs get different keys.
    """
    # Canonical salt: lower node_id first so both sides derive same key
    lo, hi = sorted([local_id, peer_id])
    salt = struct.pack(">II", lo, hi)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        info=info,
    )
    return hkdf.derive(shared_secret)


def derive_psk(raw_passphrase: str) -> bytes:
    """
    Stretch a human-readable passphrase into a 32-byte PSK with HKDF.
    Salt is fixed so every node with the same passphrase gets the same key.
    """
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=b"lora-psk-salt-v1",
        info=b"lora-psk-v1",
    )
    return hkdf.derive(raw_passphrase.encode())


# ──────────────────────────────────────────────────────────
# Encryption / Decryption
# ──────────────────────────────────────────────────────────

def encrypt(key: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    """
    Encrypt plaintext with ChaCha20-Poly1305.

    Returns: nonce (12 B) || ciphertext || tag (16 B)
    """
    nonce = os.urandom(NONCE_LEN)
    chacha = ChaCha20Poly1305(key)
    ciphertext_with_tag = chacha.encrypt(nonce, plaintext, aad or None)
    return nonce + ciphertext_with_tag


def decrypt(key: bytes, data: bytes, aad: bytes = b"") -> bytes:
    """
    Decrypt a message produced by encrypt().

    Raises cryptography.exceptions.InvalidTag on authentication failure.
    """
    if len(data) < NONCE_LEN + TAG_LEN:
        raise ValueError(f"Ciphertext too short: {len(data)} bytes")
    nonce = data[:NONCE_LEN]
    ciphertext_with_tag = data[NONCE_LEN:]
    chacha = ChaCha20Poly1305(key)
    return chacha.decrypt(nonce, ciphertext_with_tag, aad or None)


# ──────────────────────────────────────────────────────────
# Session key store
# ──────────────────────────────────────────────────────────

class KeyStore:
    """
    Manages symmetric session keys per peer node.

    In PSK mode a single key is used for all peers.
    In ECDH mode each peer gets an individually derived key after handshake.
    """

    def __init__(self, psk: Optional[bytes] = None):
        self._psk: Optional[bytes] = psk
        # peer_id (int) -> 32-byte session key
        self._sessions: dict[int, bytes] = {}

    # ── PSK helpers ────────────────────────────────────────

    @classmethod
    def from_passphrase(cls, passphrase: str) -> "KeyStore":
        return cls(psk=derive_psk(passphrase))

    @classmethod
    def from_key_file(cls, path: str) -> "KeyStore":
        raw = Path(path).read_bytes().strip()
        if len(raw) != KEY_LEN:
            raise ValueError(f"PSK file must contain exactly {KEY_LEN} raw bytes")
        return cls(psk=raw)

    def generate_psk_file(self, path: str) -> bytes:
        """Generate a random PSK and save it to path. Returns the key."""
        key = os.urandom(KEY_LEN)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(key)
        p.chmod(0o600)
        return key

    # ── ECDH session key registration ─────────────────────

    def register_session(
        self,
        peer_id: int,
        shared_secret: bytes,
        local_id: int,
    ) -> bytes:
        key = derive_session_key(shared_secret, local_id, peer_id)
        self._sessions[peer_id] = key
        return key

    # ── Key lookup ─────────────────────────────────────────

    def get_key(self, peer_id: int) -> Optional[bytes]:
        """
        Return the key to use when communicating with peer_id.
        PSK overrides per-session keys.
        """
        if self._psk:
            return self._psk
        return self._sessions.get(peer_id)

    def has_session(self, peer_id: int) -> bool:
        if self._psk:
            return True
        return peer_id in self._sessions

    def peer_ids(self) -> list[int]:
        return list(self._sessions.keys())

    # ── Persistence (session keys only — PSK stored separately) ──

    def save_sessions(self, path: str) -> None:
        data = {str(k): v.hex() for k, v in self._sessions.items()}
        Path(path).write_text(json.dumps(data))

    def load_sessions(self, path: str) -> None:
        try:
            data = json.loads(Path(path).read_text())
            self._sessions = {int(k): bytes.fromhex(v) for k, v in data.items()}
        except FileNotFoundError:
            pass
