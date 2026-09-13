"""Current-owner-authorized Ed25519 key rotation."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .key_management import OwnerKeyRecord, key_id_from_public_key, public_key_b64
from .root_of_trust import SecurityError


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class KeyRotationRequest:
    owner_id: str
    rotation_id: str
    current_key_id: str
    new_key_id: str
    new_public_key_b64: str
    version: int
    signature: str

    def signing_payload(self) -> dict[str, Any]:
        return {
            "current_key_id": self.current_key_id,
            "new_key_id": self.new_key_id,
            "new_public_key_b64": self.new_public_key_b64,
            "owner_id": self.owner_id,
            "rotation_id": self.rotation_id,
            "version": self.version,
        }


def build_rotation_request(current_key: Ed25519PrivateKey, *, owner_id: str, rotation_id: str, new_public_key: Ed25519PublicKey, version: int = 1) -> KeyRotationRequest:
    current_id = key_id_from_public_key(current_key.public_key())
    new_id = key_id_from_public_key(new_public_key)
    unsigned = KeyRotationRequest(owner_id, rotation_id, current_id, new_id, public_key_b64(new_public_key), version, "")
    signature = base64.b64encode(current_key.sign(_canonical(unsigned.signing_payload()))).decode("ascii")
    return KeyRotationRequest(owner_id, rotation_id, current_id, new_id, unsigned.new_public_key_b64, version, signature)


class KeyRegistry:
    """In-memory registry for the first DEE key lifecycle implementation."""

    def __init__(self, record: OwnerKeyRecord) -> None:
        self._records = {record.key_id: record}
        self._owner_id = record.owner_id
        self._seen_rotations: set[str] = set()

    @property
    def active(self) -> OwnerKeyRecord:
        records = [r for r in self._records.values() if r.status == "active"]
        if len(records) != 1:
            raise SecurityError("DEE owner registry must have exactly one active key")
        return records[0]

    def authorize_rotation(self, request: KeyRotationRequest, current_public_key: Ed25519PublicKey) -> None:
        if request.owner_id != self._owner_id or request.version < 1:
            raise SecurityError("rotation owner/version mismatch")
        if request.rotation_id in self._seen_rotations:
            raise SecurityError("rotation replay detected")
        if request.current_key_id != self.active.key_id or key_id_from_public_key(current_public_key) != self.active.key_id:
            raise SecurityError("rotation must be signed by the active owner key")
        if request.new_key_id in self._records:
            raise SecurityError("new owner key already exists")
        try:
            current_public_key.verify(base64.b64decode(request.signature.encode("ascii"), validate=True), _canonical(request.signing_payload()))
            raw = base64.b64decode(request.new_public_key_b64.encode("ascii"), validate=True)
            derived = key_id_from_public_key(Ed25519PublicKey.from_public_bytes(raw))
        except Exception as exc:
            raise SecurityError("invalid key rotation signature or public key") from exc
        if derived != request.new_key_id:
            raise SecurityError("new key fingerprint mismatch")

    def apply_rotation(self, request: KeyRotationRequest, current_public_key: Ed25519PublicKey) -> OwnerKeyRecord:
        self.authorize_rotation(request, current_public_key)
        old = self.active
        self._records[old.key_id] = OwnerKeyRecord(old.owner_id, old.key_id, old.public_key_b64, "revoked", old.created_at, old.rotated_from)
        new = OwnerKeyRecord(self._owner_id, request.new_key_id, request.new_public_key_b64, "active", rotated_from=old.key_id)
        self._records[new.key_id] = new
        self._seen_rotations.add(request.rotation_id)
        return new
