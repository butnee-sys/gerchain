"""Deterministic DEE genesis anchor for the root-of-trust boundary."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


class GenesisError(ValueError):
    """Raised when a DEE genesis anchor is invalid."""


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class GenesisAnchor:
    owner_id: str
    public_key: str
    policy_version: str
    genesis_hash: str

    def signing_payload(self) -> dict[str, str]:
        return {
            "owner_id": self.owner_id,
            "policy_version": self.policy_version,
            "public_key": self.public_key,
        }


def build_genesis_anchor(*, owner_id: str, public_key: str, policy_version: str) -> GenesisAnchor:
    if not owner_id or not public_key or not policy_version:
        raise GenesisError("genesis identity, public key, and policy version are required")
    payload = {
        "owner_id": owner_id,
        "policy_version": policy_version,
        "public_key": public_key,
    }
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return GenesisAnchor(owner_id, public_key, policy_version, digest)


def verify_genesis_anchor(anchor: GenesisAnchor) -> bool:
    if not anchor.owner_id or not anchor.public_key or not anchor.policy_version:
        return False
    expected = build_genesis_anchor(
        owner_id=anchor.owner_id,
        public_key=anchor.public_key,
        policy_version=anchor.policy_version,
    ).genesis_hash
    return anchor.genesis_hash == expected
