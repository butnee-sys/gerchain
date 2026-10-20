"""Protected contract governance compatibility boundary.

This module provides the small executable contract used by DEE proof collection.
It does not create a second authority; it verifies ownership, policy scope, and
payload integrity before allowing the change to be considered governed.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .authorization import AuthorizationPolicy
from .root_of_trust import RootOfTrust, SecurityError


def _hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class ProtectedContract:
    contract_id: str
    version: int
    payload: Mapping[str, Any]
    owner_id: str
    payload_hash: str

    @classmethod
    def build(cls, *, contract_id: str, version: int, payload: Mapping[str, Any], owner_id: str) -> "ProtectedContract":
        if not contract_id or version < 1 or not owner_id:
            raise SecurityError("invalid protected contract")
        return cls(contract_id, version, dict(payload), owner_id, _hash(payload))

    def verify(self, payload: Mapping[str, Any]) -> bool:
        return _hash(payload) == self.payload_hash


def authorize_contract_change(*, root: RootOfTrust, contract: ProtectedContract, policy: AuthorizationPolicy, change_kind: str) -> None:
    if contract.owner_id != root.owner_id:
        raise SecurityError("contract owner does not match Root of Trust")
    if contract.version < policy.minimum_version:
        raise SecurityError("contract version is below authorization floor")
    if change_kind not in policy.allowed_change_kinds:
        raise SecurityError("contract change kind is not allowed")
    if not contract.verify(contract.payload):
        raise SecurityError("contract payload integrity verification failed")
