"""Full DEE governed-operation proof: one fail-closed boundary across the stack."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class DEEE2EProofError(SecurityError):
    """Raised when the complete DEE governance proof is incomplete."""


@dataclass(frozen=True)
class DEEE2EProof:
    genesis_verified: bool
    owner_verified: bool
    governance_verified: bool
    identity_verified: bool
    contract_verified: bool
    evidence_verified: bool
    gateway_verified: bool
    connector_verified: bool
    exim_verified: bool
    core_verified: bool
    escrow_verified: bool
    witness_verified: bool
    settlement_verified: bool
    audit_verified: bool
    recovery_verified: bool
    release_verified: bool

    def require_complete(self) -> None:
        failed = [name for name, value in vars(self).items() if not value]
        if failed:
            raise DEEE2EProofError("incomplete DEE E2E proof: " + ", ".join(failed))


def require_dee_e2e_proof(
    *,
    root: RootOfTrust,
    owner_id: str,
    proof: DEEE2EProof,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Fail closed unless every governed stage and Trinity are proven."""
    if owner_id != root.owner_id:
        raise DEEE2EProofError("E2E owner is not bound to DEE Root of Trust")
    try:
        require_trinity(trinity_proof)
    except TrinityError as exc:
        raise DEEE2EProofError(str(exc)) from exc
    proof.require_complete()


__all__ = ["DEEE2EProof", "DEEE2EProofError", "require_dee_e2e_proof"]
