from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from core.economic_state import EconomicStateFingerprint, fingerprint_relevant_state, state_matches
from persistence.atomic_release import (
    AtomicReleaseResult,
    PostgreSQLAtomicRelease,
    ReleaseAccount,
    ReleaseEscrow,
)


class StaleDecisionError(RuntimeError):
    """Raised when an approved decision no longer matches relevant state."""


@dataclass(frozen=True)
class ReleaseDecisionState:
    fingerprint: EconomicStateFingerprint


def release_decision_state(*, source: ReleaseAccount, escrow: ReleaseEscrow, amount: int) -> ReleaseDecisionState:
    state = {
        "source_account": source.account_id,
        "source_balance": source.balance,
        "escrow_id": escrow.escrow_id,
        "escrow_state": escrow.state,
        "escrow_amount": escrow.amount,
        "requested_amount": amount,
    }
    return ReleaseDecisionState(
        fingerprint=fingerprint_relevant_state(version="release-state-v1", state=state)
    )


class _ReusedSessionContext:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc, tb):
        return False


class DecisionBoundPostgreSQLRelease:
    """Thin decision-validity guard over the existing atomic release engine."""

    def __init__(self, release: PostgreSQLAtomicRelease):
        self._release = release

    def release(
        self,
        *,
        decision_state: EconomicStateFingerprint,
        idempotency_key: str,
        transaction_id: str,
        escrow_id: str,
        source: str,
        destination: str,
        amount: int,
        decision_status: str,
        authorization_status: str,
        trinity_proof: dict[str, bool],
        evidence_verified: bool,
    ) -> AtomicReleaseResult:
        with self._release.session_factory() as session:
            escrow_row = session.execute(
                select(ReleaseEscrow).where(ReleaseEscrow.escrow_id == escrow_id).with_for_update()
            ).scalar_one()
            source_row = session.execute(
                select(ReleaseAccount).where(ReleaseAccount.account_id == source).with_for_update()
            ).scalar_one()

            current = release_decision_state(
                source=source_row,
                escrow=escrow_row,
                amount=amount,
            ).fingerprint
            if not state_matches(decision=decision_state, current=current):
                raise StaleDecisionError("release decision is stale: relevant economic state changed")

            guarded_release = PostgreSQLAtomicRelease(
                lambda: _ReusedSessionContext(session),
                processing_lease_seconds=self._release.processing_lease_seconds,
            )
            return guarded_release.release(
                idempotency_key=idempotency_key,
                transaction_id=transaction_id,
                escrow_id=escrow_id,
                source=source,
                destination=destination,
                amount=amount,
                decision_status=decision_status,
                authorization_status=authorization_status,
                trinity_proof=trinity_proof,
                evidence_verified=evidence_verified,
            )


__all__ = [
    "DecisionBoundPostgreSQLRelease",
    "ReleaseDecisionState",
    "StaleDecisionError",
    "release_decision_state",
]
