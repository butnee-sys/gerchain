from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from persistence.atomic_release import AtomicReleaseResult, PostgreSQLAtomicRelease


@dataclass(frozen=True)
class ReleaseRequest:
    idempotency_key: str
    transaction_id: str
    escrow_id: str
    source: str
    destination: str
    amount: int
    decision_status: str
    authorization_status: str
    trinity_proof: Mapping[str, bool]
    evidence_verified: bool


class PostgreSQLReleaseAdapter:
    """Runtime boundary for durable release; does not replace GerChain's in-memory mode."""

    def __init__(self, release: PostgreSQLAtomicRelease):
        self.release_engine = release

    def execute(self, request: ReleaseRequest) -> AtomicReleaseResult:
        return self.release_engine.release(
            idempotency_key=request.idempotency_key,
            transaction_id=request.transaction_id,
            escrow_id=request.escrow_id,
            source=request.source,
            destination=request.destination,
            amount=request.amount,
            decision_status=request.decision_status,
            authorization_status=request.authorization_status,
            trinity_proof=request.trinity_proof,
            evidence_verified=request.evidence_verified,
        )


__all__ = ["ReleaseRequest", "PostgreSQLReleaseAdapter"]
