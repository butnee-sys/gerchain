"""DEE-governed money settlement authorization."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .root_of_trust import RootOfTrust, SecurityError
from .trinity import TrinityError, require_trinity


class SettlementGovernanceError(SecurityError):
    """Raised when monetary settlement is not authorized by DEE."""


@dataclass(frozen=True)
class SettlementAuthorization:
    transaction_id: str
    escrow_id: str
    owner_id: str
    authorized: bool
    evidence_verified: bool


def authorize_settlement(*, root: RootOfTrust, authorization: SettlementAuthorization, trinity_proof: Mapping[str, bool]) -> None:
    """Fail-closed gate before any ledger/escrow settlement mutation."""
    if not authorization.transaction_id:
        raise SettlementGovernanceError("transaction_id is required")
    if not authorization.escrow_id:
        raise SettlementGovernanceError("escrow_id is required")
    if authorization.owner_id != root.owner_id:
        raise SettlementGovernanceError("settlement owner is not bound to DEE Root of Trust")
    if not authorization.authorized:
        raise SettlementGovernanceError("settlement authorization is required")
    if not authorization.evidence_verified:
        raise SettlementGovernanceError("settlement evidence verification is required")
    try:
        require_trinity(trinity_proof)
    except TrinityError as exc:
        raise SettlementGovernanceError(str(exc)) from exc


__all__ = ["SettlementAuthorization", "SettlementGovernanceError", "authorize_settlement"]
