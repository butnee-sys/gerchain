"""Owner key lifecycle helpers for the Digital Escrow Ecosystem.

Private keys are operational secrets. This module can generate/load them in
memory, but never stores private key material in the repository, database,
or configuration.
"""
from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .root_of_trust import SecurityError


def key_id_from_public_key(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return hashlib.sha256(raw).hexdigest()


def public_key_b64(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(raw).decode("ascii")


def generate_owner_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    private = Ed25519PrivateKey.generate()
    return private, private.public_key()


def load_private_key(path: str | os.PathLike[str]) -> Ed25519PrivateKey:
    """Load an operational PEM key without persisting or copying it elsewhere."""
    try:
        key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
    except Exception as exc:
        raise SecurityError("unable to load owner private key") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise SecurityError("owner private key must be Ed25519")
    return key


@dataclass(frozen=True)
class OwnerKeyRecord:
    owner_id: str
    key_id: str
    public_key_b64: str
    status: str = "active"
    created_at: str | None = None
    rotated_from: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"active", "revoked", "pending"}:
            raise SecurityError("invalid owner key status")
        if not self.owner_id or not self.key_id or not self.public_key_b64:
            raise SecurityError("owner key record is incomplete")
