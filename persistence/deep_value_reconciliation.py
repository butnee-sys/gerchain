from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.atomic_ledger import LedgerMovementModel
from persistence.atomic_release import ReleaseAccount
from persistence.atomic_settlement import AccountBalance
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.recovery_outbox import OutboxEvent
from persistence.transactional_outbox import deterministic_event_id
from persistence.value_reconciliation import _snapshot_canonical


@dataclass(frozen=True)
class ValueTruthIssue:
    code: str
    transaction_id: str | None
    detail: str


@dataclass(frozen=True)
class DeepValueTruthReport:
    canonical_movement_count: int
    outbox_count: int
    idempotency_count: int
    issues: tuple[ValueTruthIssue, ...]
    matched: bool


def deep_reconcile_value_truth(session: Session) -> DeepValueTruthReport:
    """Reconcile canonical movements against durable evidence without mutation.

    This is an evidence audit, not a second value authority.
    """
    issues: list[ValueTruthIssue] = []
    movements = list(session.execute(select(LedgerMovementModel)).scalars())
    outboxes = list(session.execute(select(OutboxEvent)).scalars())
    idempotencies = list(session.execute(select(DurableIdempotencyRecord)).scalars())

    outbox_by_id = {row.event_id: row for row in outboxes}
    idem_by_key = {row.key: row for row in idempotencies}

    seen: set[str] = set()
    for movement in movements:
        tx = movement.transaction_id
        if tx in seen:
            issues.append(ValueTruthIssue("DUPLICATE_TRANSACTION_MOVEMENT", tx, "duplicate canonical movement"))
        seen.add(tx)

        if movement.amount <= 0:
            issues.append(ValueTruthIssue("INVALID_AMOUNT", tx, "canonical movement amount must be positive"))

        event_id = deterministic_event_id(
            f"gerchain_{_operation_from_transaction(tx)}",
            tx,
        )
        if not any(row.aggregate_id in {movement.source, movement.destination} and row.payload_json for row in outboxes if tx in row.event_id):
            issues.append(ValueTruthIssue("MISSING_OUTBOX_EVIDENCE", tx, "no outbox evidence associated with transaction"))

        if not any(tx in row.key for row in idempotencies):
            issues.append(ValueTruthIssue("MISSING_IDEMPOTENCY_EVIDENCE", tx, "no durable idempotency record associated with transaction"))

    return DeepValueTruthReport(
        canonical_movement_count=len(movements),
        outbox_count=len(outboxes),
        idempotency_count=len(idempotencies),
        issues=tuple(issues),
        matched=not issues,
    )


def _operation_from_transaction(transaction_id: str) -> str:
    """Best-effort operation extraction for evidence reconciliation only."""
    lower = transaction_id.lower()
    for operation in ("fund", "lock", "release", "refund", "cancel", "settlement"):
        if operation in lower:
            return operation
    return "movement"
