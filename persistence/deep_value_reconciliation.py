from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.atomic_ledger import LedgerMovementModel
from persistence.atomic_value_transaction import TransactionWitness
from persistence.durable_idempotency import DurableIdempotencyRecord
from persistence.escrow_aggregate import CanonicalEscrow
from persistence.recovery_outbox import OutboxEvent


@dataclass(frozen=True)
class ValueTruthIssue:
    code: str
    transaction_id: str | None
    detail: str


@dataclass(frozen=True)
class DeepValueTruthReport:
    canonical_movement_count: int
    witness_count: int
    outbox_count: int
    idempotency_count: int
    escrow_count: int
    issues: tuple[ValueTruthIssue, ...]

    @property
    def matched(self) -> bool:
        return not self.issues


def _expected_integrity_hash(movement: LedgerMovementModel) -> str:
    material = json.dumps(
        {
            "transaction_id": movement.transaction_id,
            "operation": movement.operation,
            "escrow_id": movement.escrow_id,
            "source": movement.source,
            "destination": movement.destination,
            "amount": movement.amount,
            "currency": movement.currency,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def deep_reconcile_value_truth(session: Session) -> DeepValueTruthReport:
    """Read-only two-way reconciliation of canonical transaction evidence.

    A movement must have matching escrow, witness, outbox and completed
    idempotency evidence. Evidence records must not exist without their
    corresponding canonical movement.
    """
    movements = list(session.execute(select(LedgerMovementModel)).scalars())
    witnesses = list(session.execute(select(TransactionWitness)).scalars())
    outboxes = list(session.execute(select(OutboxEvent)).scalars())
    idempotencies = list(session.execute(select(DurableIdempotencyRecord)).scalars())
    escrows = list(session.execute(select(CanonicalEscrow)).scalars())

    issues: list[ValueTruthIssue] = []
    movement_by_tx = {m.transaction_id: m for m in movements}
    witness_by_tx = {w.transaction_id: w for w in witnesses}
    idem_by_key = {i.key: i for i in idempotencies}
    escrow_by_id = {e.id: e for e in escrows}

    outbox_by_tx: dict[str, list[OutboxEvent]] = {}
    for event in outboxes:
        parts = event.event_id.split(":", 1)
        if len(parts) == 2:
            outbox_by_tx.setdefault(parts[1], []).append(event)

    def issue(code: str, tx: str | None, detail: str) -> None:
        issues.append(ValueTruthIssue(code, tx, detail))

    event_type_by_operation = {
        "FUND": "GERCHAIN_FUNDED",
        "RELEASE": "GERCHAIN_RELEASED",
        "REFUND": "GERCHAIN_REFUNDED",
        "CANCEL": "GERCHAIN_CANCELLED",
    }

    for movement in movements:
        tx = movement.transaction_id
        if movement.amount <= 0:
            issue("INVALID_AMOUNT", tx, "canonical movement amount must be positive")
        if not movement.operation:
            issue("MISSING_OPERATION", tx, "canonical movement operation is missing")

        # Escrow-bound value operations require the canonical escrow/evidence
        # graph. SETTLEMENT is a direct ledger operation by design and therefore
        # has no escrow aggregate, witness, outbox, or escrow-scoped idempotency.
        escrow_bound = movement.operation != "SETTLEMENT"
        if escrow_bound:
            if not movement.escrow_id:
                issue("MISSING_ESCROW_ID", tx, "canonical movement escrow reference is missing")
            elif movement.escrow_id not in escrow_by_id:
                issue("ORPHAN_ESCROW_REFERENCE", tx, "movement references a missing canonical escrow")

            witness = witness_by_tx.get(tx)
            if witness is None:
                issue("UNWITNESSED_MOVEMENT", tx, "movement has no witness")
            elif (witness.event_type, witness.escrow_id, witness.amount) != (
                event_type_by_operation.get(movement.operation, f"GERCHAIN_{movement.operation}"),
                movement.escrow_id,
                movement.amount,
            ):
                issue("WITNESS_MISMATCH", tx, "witness does not match canonical movement")

            matching_outboxes = outbox_by_tx.get(tx, [])
            if not matching_outboxes:
                issue("UNOUTBOXED_MOVEMENT", tx, "movement has no outbox evidence")
            elif not any(
                e.aggregate_id == movement.escrow_id
                and e.event_type == f"GERCHAIN_{movement.operation}"
                for e in matching_outboxes
            ):
                issue(
                    "OUTBOX_AGGREGATE_MISMATCH",
                    tx,
                    "outbox type or aggregate does not match canonical movement",
                )

            idem = idem_by_key.get(tx)
            if idem is None:
                issue("MISSING_IDEMPOTENCY_EVIDENCE", tx, "movement has no durable idempotency record")
            elif idem.state != "COMPLETED":
                issue("INCOMPLETE_IDEMPOTENCY", tx, "movement idempotency record is not COMPLETED")

        if not movement.integrity_hash:
            issue("MISSING_INTEGRITY_HASH", tx, "movement integrity hash is missing")
        elif movement.integrity_hash != _expected_integrity_hash(movement):
            issue("INTEGRITY_HASH_MISMATCH", tx, "movement integrity hash does not match canonical fields")

    # Witness and outbox also represent state-only operations (for example
    # LOCK), so reverse orphan checks apply only to value-moving event types.
    value_event_types = {
        "GERCHAIN_FUNDED",
        "GERCHAIN_RELEASED",
        "GERCHAIN_REFUNDED",
        "GERCHAIN_CANCELLED",
    }

    for witness in witnesses:
        if (
            witness.event_type in value_event_types
            and witness.transaction_id not in movement_by_tx
        ):
            issue(
                "ORPHAN_WITNESS",
                witness.transaction_id,
                "value-moving witness has no canonical movement",
            )

    for event in outboxes:
        if event.event_type not in value_event_types:
            continue
        parts = event.event_id.split(":", 1)
        tx = parts[1] if len(parts) == 2 else None
        if tx is None or tx not in movement_by_tx:
            issue("ORPHAN_OUTBOX", tx, "value-moving outbox event has no canonical movement")

    # Idempotency is also used by state-only operations. A completed record
    # cannot be classified as an orphan solely from its key because the
    # current durable record does not persist operation type. Movement-side
    # checks therefore remain authoritative for value transactions.

    return DeepValueTruthReport(
        canonical_movement_count=len(movements),
        witness_count=len(witnesses),
        outbox_count=len(outboxes),
        idempotency_count=len(idempotencies),
        escrow_count=len(escrows),
        issues=tuple(issues),
    )


__all__ = ["ValueTruthIssue", "DeepValueTruthReport", "deep_reconcile_value_truth"]
