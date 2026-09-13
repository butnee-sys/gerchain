"""Cryptographic trust anchor for protected DEE changes.

Ed25519 is used through the ``cryptography`` package. The private key is an
external operational secret: it is never accepted as configuration from the
repository and is never persisted by this module.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Mapping

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError as exc:  # fail closed when the security dependency is absent
    raise RuntimeError(
        "DEE security requires the 'cryptography' package; install it before use."
    ) from exc


class SecurityError(ValueError):
    """Raised when a protected DEE operation cannot be authenticated."""


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _b64decode(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:
        raise SecurityError("invalid base64 security material") from exc


@dataclass(frozen=True)
class SignedChange:
    """A signed, replay-resistant description of a protected change."""

    owner_id: str
    change_id: str
    version: int
    payload_hash: str
    signature: str

    def signing_payload(self) -> dict[str, Any]:
        return {
            "change_id": self.change_id,
            "owner_id": self.owner_id,
            "payload_hash": self.payload_hash,
            "version": self.version,
        }


class RootOfTrust:
    """Verify DEE changes against a pinned owner Ed25519 public key."""

    algorithm = "Ed25519"

    def __init__(self, owner_id: str, public_key_b64: str) -> None:
        if not owner_id or not public_key_b64:
            raise SecurityError("owner_id and public_key_b64 are required")
        key_bytes = _b64decode(public_key_b64)
        try:
            self._public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
        except ValueError as exc:
            raise SecurityError("owner public key must be a 32-byte Ed25519 key") from exc
        self.owner_id = owner_id
        self.public_key_b64 = public_key_b64

    @classmethod
    def from_pem(cls, owner_id: str, pem: bytes) -> "RootOfTrust":
        try:
            key = serialization.load_pem_public_key(pem)
            raw = key.public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            )
        except Exception as exc:
            raise SecurityError("invalid Ed25519 public key PEM") from exc
        return cls(owner_id, base64.b64encode(raw).decode("ascii"))

    def verify(self, change: SignedChange) -> bool:
        if change.owner_id != self.owner_id:
            return False
        if change.version < 1 or not change.change_id or not change.payload_hash:
            return False
        try:
            self._public_key.verify(
                _b64decode(change.signature), _canonical_bytes(change.signing_payload())
            )
            return True
        except (InvalidSignature, SecurityError):
            return False

    def require_valid(self, change: SignedChange) -> None:
        if not self.verify(change):
            raise SecurityError("DEE change is not authorized by the Root of Trust")
