"""External-key release signing primitives for the DEE security boundary.

Private keys are accepted only as runtime objects/bytes and are never persisted
or serialized by this module.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .root_of_trust import SecurityError


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _b64decode(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except Exception as exc:
        raise SecurityError("invalid base64 release signature") from exc


@dataclass(frozen=True)
class SignedRelease:
    """Owner-signed release authorization bound to one manifest and commit."""

    release_id: str
    owner_id: str
    manifest_hash: str
    commit_sha: str
    signature: str

    def signing_payload(self) -> dict[str, str]:
        return {
            "commit_sha": self.commit_sha,
            "manifest_hash": self.manifest_hash,
            "owner_id": self.owner_id,
            "release_id": self.release_id,
        }


def _private_key(value: Ed25519PrivateKey | bytes) -> Ed25519PrivateKey:
    if isinstance(value, Ed25519PrivateKey):
        return value
    if isinstance(value, bytes):
        try:
            return Ed25519PrivateKey.from_private_bytes(value)
        except ValueError as exc:
            raise SecurityError("invalid Ed25519 private key") from exc
    raise TypeError("private_key must be an Ed25519PrivateKey or 32 raw bytes")


def sign_release(
    private_key: Ed25519PrivateKey | bytes,
    *,
    release_id: str,
    owner_id: str,
    manifest_hash: str,
    commit_sha: str,
) -> SignedRelease:
    if not all((release_id, owner_id, manifest_hash, commit_sha)):
        raise SecurityError("release signing fields are required")
    key = _private_key(private_key)
    unsigned = SignedRelease(
        release_id=release_id,
        owner_id=owner_id,
        manifest_hash=manifest_hash,
        commit_sha=commit_sha,
        signature="",
    )
    signature = base64.b64encode(key.sign(_canonical_bytes(unsigned.signing_payload()))).decode("ascii")
    return SignedRelease(**{**unsigned.__dict__, "signature": signature})


def verify_release(release: SignedRelease, public_key_b64: str) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(_b64decode(public_key_b64))
        public_key.verify(_b64decode(release.signature), _canonical_bytes(release.signing_payload()))
        return True
    except (InvalidSignature, ValueError, SecurityError):
        return False


def export_public_key_b64(private_key: Ed25519PrivateKey | bytes) -> str:
    key = _private_key(private_key)
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(public).decode("ascii")
