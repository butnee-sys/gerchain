from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.atomic_value_transaction import record_witness_in_transaction
from persistence.durable_idempotency import begin_in_transaction, complete_in_transaction
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.transactional_outbox import deterministic_event_id, enqueue_in_transaction


def create_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    source: str,
    beneficiary: str,
    refund_destination: str,
    amount: int,
    currency: str,
    condition: str | None = None,
) -> dict[str, Any]:
    """Atomically create canonical escrow truth and its evidence; never moves value."""
    if not transaction_id:
        raise ValueError("transaction_id is required")
    if not escrow_id:
        raise ValueError("escrow_id is required")
    if not source or not beneficiary or not refund_destination:
        raise ValueError("source, beneficiary and refund_destination are required")
    if source == beneficiary:
        raise ValueError("source and beneficiary must differ")
    if amount <= 0:
        raise ValueError("escrow amount must be positive")
    if not currency:
        raise ValueError("currency is required")

    payload = {
        "operation": "CREATE",
        "escrow_id": escrow_id,
        "source": source,
        "beneficiary": beneficiary,
        "refund_destination": refund_destination,
        "amount": amount,
        "currency": currency,
        "condition": condition,
    }
    replay = begin_in_transaction(session, key=transaction_id, payload=payload)
    if replay is not None:
        return {"replayed": True, "result": json.loads(replay)}

    existing = session.execute(
        select(CanonicalEscrow).where(CanonicalEscrow.id == escrow_id).with_for_update()
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("escrow ID already exists under canonical authority")

    now = datetime.now(timezone.utc)
    session.add(
        CanonicalEscrow(
            id=escrow_id,
            sender_address=source,
            receiver_address=beneficiary,
            refund_destination=refund_destination,
            amount=amount,
            currency=currency,
            condition_desc=condition,
            state=EscrowState.CREATED.value,
            version=0,
            created_at=now,
            updated_at=now,
        )
    )
    record_witness_in_transaction(
        session,
        transaction_id=transaction_id,
        event_type="GERCHAIN_CREATED",
        escrow_id=escrow_id,
        amount=0,
    )
    result = {
        "escrow_id": escrow_id,
        "state": EscrowState.CREATED.value,
        "amount": amount,
        "currency": currency,
        "version": 0,
        "replayed": False,
        "value_movement": False,
    }
    enqueue_in_transaction(
        session,
        event_id=deterministic_event_id("GERCHAIN_CREATED", transaction_id),
        event_type="GERCHAIN_CREATED",
        aggregate_id=escrow_id,
        payload={
            "transaction_id": transaction_id,
            "escrow_id": escrow_id,
            "operation": "CREATE",
            "value_movement": False,
            "amount": 0,
            "source": source,
            "destination": None,
            "currency": currency,
        },
    )
    complete_in_transaction(
        session,
        key=transaction_id,
        payload=payload,
        result_json=json.dumps(result, sort_keys=True, separators=(",", ":")),
    )
    return result


def create_escrow(session_factory, **kwargs: Any) -> dict[str, Any]:
    with session_factory() as session:
        result = create_escrow_in_transaction(session, **kwargs)
        session.commit()
        return result


__all__ = ["create_escrow_in_transaction", "create_escrow"]
