"""DEE contract governance: bind protected contracts to the Root of Trust."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .authorization import AuthorizationPolicy
from .root_of_trust import RootOfTrust, SecurityError, SignedChange


class ContractGovernanceError(SecurityError):
    """Raised when a protected contract fails DEE governance."""


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class ProtectedContract:
    contract_id: str
    version: int
    contract_hash: str
    owner_id: str

    @classmethod
    def build(
        cls,
        *,
        contract_id: str,
        version: int,
        specification: Mapping[str, Any],
        root: RootOfTrust,
    ) -> "ProtectedContract":
        if not contract_id or version < 1:
            raise ContractGovernanceError("contract_id and positive version are required")
        return cls(
            contract_id=contract_id,
            version=version,
            contract_hash=sha256(_canonical_bytes(specification)).hexdigest(),
            owner_id=root.owner_id,
        )

    def verify(self, *, root: RootOfTrust, specification: Mapping[str, Any]) -> bool:
        if self.owner_id != root.owner_id or self.version < 1:
            return False
        return self.contract_hash == sha256(_canonical_bytes(specification)).hexdigest()


def authorize_contract_change(
    *,
    root: RootOfTrust,
    policy: AuthorizationPolicy,
    change: SignedChange,
    contract: ProtectedContract,
    paths: tuple[str, ...],
    change_kind: str = "rule",
) -> None:
    """Require both Root-of-Trust authorization and contract ownership binding."""
    if contract.owner_id != root.owner_id:
        raise ContractGovernanceError("contract owner is not bound to the DEE Root of Trust")
    policy.check(root=root, change=change, paths=paths, change_kind=change_kind)


__all__ = [
    "ContractGovernanceError",
    "ProtectedContract",
    "authorize_contract_change",
]
