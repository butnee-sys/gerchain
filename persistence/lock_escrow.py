from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from persistence.atomic_value_transaction import (
    AtomicValueTransaction,
    record_witness_in_transaction,
)
from persistence.durable_idempotency import begin_in_transaction, complete_in_transaction
from persistence.escrow_aggregate import EscrowState
from persistence.transactional_outbox import deterministic_event_id, enqueue_in_transaction


def lock_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Atomically lock a FUNDED escrow without moving value."""
    idempotency_payload = {
        "escrow_id": escrow_id,
        "operation": "LOCK",
        **dict(payload or {}),
    }
    replay = begin_in_transaction(
        session,
        key=transaction_id,
        payload=idempotency_payload,
    )
    if replay is not None:
        return {"replayed": True, "result": replay}

    from persistence.escrow_aggregate import transition_escrow

    transition_escrow(
        session,
        escrow_id,
        EscrowState.FUNDED,
        EscrowState.LOCKED,
    )
    record_witness_in_transaction(
        session,
        transaction_id=transaction_id,
        event_type="GERCHAIN_LOCKED",
        escrow_id=escrow_id,
        amount=0,
    )
    enqueue_in_transaction(
        session,
        event_id=deterministic_event_id("GERCHAIN_LOCKED", transaction_id),
        event_type="GERCHAIN_LOCKED",
        aggregate_id=escrow_id,
        payload={"transaction_id": transaction_id, "escrow_id": escrow_id, **dict(payload or {})},
    )
    complete_in_transaction(
        session,
        key=transaction_id,
        payload=idempotency_payload,
        result_json='{"status":"LOCKED","value_movement":false}',
    )
    return {"replayed": False, "status": "LOCKED", "value_movement": False}


__all__ = ["lock_escrow_in_transaction"]
