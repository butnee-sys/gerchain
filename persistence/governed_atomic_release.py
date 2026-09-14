from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from persistence.atomic_release import AtomicReleaseResult, PostgreSQLAtomicRelease


class ReleaseGovernanceError(RuntimeError):
    """Raised when release governance is not fully satisfied."""


@dataclass(frozen=True)
class ReleaseGovernance:
    decision: str
    authorization: str
    trust: str
    transparency: str
    performance: str
    evidence_verified: bool

    def require_pass(self) -> None:
        if self.decision != "APPROVE":
            raise ReleaseGovernanceError("release decision is not APPROVE")
        if self.authorization != "AUTHORIZED":
            raise ReleaseGovernanceError("release authorization is not AUTHORIZED")
        if any(value != "PASS" for value in (self.trust, self.transparency, self.performance)):
            raise ReleaseGovernanceError("G-3 escrow trinity is not PASS")
        if not self.evidence_verified:
            raise ReleaseGovernanceError("release evidence is not verified")


class GovernedAtomicRelease:
    """Fail-closed governance facade; value movement remains in AtomicRelease."""

    def __init__(self, release: PostgreSQLAtomicRelease):
        self._release = release

    def release(self, *, governance: ReleaseGovernance, idempotency_key: str, transaction_id: str, escrow_id: str, source: str, destination: str, amount: int) -> AtomicReleaseResult:
        governance.require_pass()
        return self._release.release(
            idempotency_key=idempotency_key,
            transaction_id=transaction_id,
            escrow_id=escrow_id,
            source=source,
            destination=destination,
            amount=amount,
        )


__all__ = ["ReleaseGovernanceError", "ReleaseGovernance", "GovernedAtomicRelease"]
