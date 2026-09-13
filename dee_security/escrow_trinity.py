"""Fail-closed Trinity enforcement for escrow execution boundaries."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class EscrowTrinityError(SecurityError):
    """Raised when an escrow transition lacks a complete Trinity proof."""


@dataclass(frozen=True)
class EscrowExecutionProof:
    escrow_id: str
    transition_id: str
    authorized: bool
    evidence_verified: bool
    witness_ready: bool


def require_escrow_trinity(
    *,
    root: RootOfTrust,
    owner_id: str,
    proof: EscrowExecutionProof,
    trinity_proof: Mapping[str, bool],
) -> None:
    """Gate an escrow execution transition before the engine mutates state."""
    if not proof.escrow_id or not proof.transition_id:
        raise EscrowTrinityError("escrow_id and transition_id are required")
    if owner_id != root.owner_id:
        raise EscrowTrinityError("escrow execution is not bound to DEE Root of Trust")
    if not proof.authorized:
        raise EscrowTrinityError("escrow execution authorization is required")
    if not proof.evidence_verified:
        raise EscrowTrinityError("verified evidence is required before escrow execution")
    if not proof.witness_ready:
        raise EscrowTrinityError("witness readiness is required before escrow execution")
    try:
        require_trinity(trinity_proof)
    except TrinityError as exc:
        raise EscrowTrinityError(str(exc)) from exc


__all__ = ["EscrowTrinityError", "EscrowExecutionProof", "require_escrow_trinity"]
