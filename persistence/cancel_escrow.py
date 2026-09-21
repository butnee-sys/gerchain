from __future__ import annotations

import json
from typing import Any, Mapping

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction
from persistence.durable_idempotency import get_existing_in_transaction, begin_in_transaction, complete_in_transaction
from persistence.escrow_aggregate import EscrowState, transition_escrow


def cancel_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Cancel an escrow using only its authoritative lifecycle destinations.

    CREATED cancellation is state-only. FUNDED cancellation reverses the
    funding movement from the escrow account to the original sender.
    """
    from sqlalchemy import select
    from persistence.escrow_aggregate import CanonicalEscrow

    escrow = session.execute(
        select(CanonicalEscrow)
        .where(CanonicalEscrow.id == escrow_id)
        .with_for_update()
    ).scalar_one()

    state = EscrowState(escrow.state)

    if not escrow.currency:
        raise ValueError("escrow currency is required for cancellation")

    destination = escrow.sender_address
    amount = int(escrow.amount)

    # Keep the idempotency fingerprint stable across the CREATED/FUNDED -> CANCELLED
    # transition so a completed cancellation can be replayed after state mutation.
    idempotency_payload = {
        "escrow_id": escrow_id,
        "operation": "CANCEL",
        "source": escrow_id,
        "destination": destination,
        "amount": amount,
        "currency": escrow.currency,
        **dict(payload or {}),
    }

    existing_result = get_existing_in_transaction(
        session,
        key=transaction_id,
        payload=idempotency_payload,
    )
    if existing_result is not None:
        return {"replayed": True, "result": existing_result}

    if state not in (EscrowState.CREATED, EscrowState.FUNDED):
        raise ValueError(f"escrow {escrow_id} cannot be cancelled from {state.value}")
    existing_result = get_existing_in_transaction(
        session,
        key=transaction_id,
        payload=idempotency_payload,
    )
    if existing_result is not None:
        return {"replayed": True, "result": existing_result}


    if state == EscrowState.CREATED:
        replay = begin_in_transaction(
            session,
            key=transaction_id,
            payload=idempotency_payload,
        )
        if replay is not None:
            return {"replayed": True, "result": replay}
        transition_escrow(
            session, escrow_id, EscrowState.CREATED, EscrowState.CANCELLED
        )
        result = {
            "status": "CANCELLED",
            "value_movement": False,
            "amount": 0,
        }
    else:
        result = AtomicValueTransaction(session).transfer_and_transition(
            transaction_id=transaction_id,
            escrow_id=escrow_id,
            source=escrow_id,
            destination=destination,
            amount=amount,
            currency=escrow.currency,
            expected_state=EscrowState.FUNDED,
            new_state=EscrowState.CANCELLED,
            ledger_transfer=ledger_transfer,
            event_type="GERCHAIN_CANCELLED",
            idempotency_payload=idempotency_payload,
            payload={
                "transaction_id": transaction_id,
                "escrow_id": escrow_id,
                "source": escrow_id,
                "destination": destination,
                "amount": amount,
                "currency": escrow.currency,
                **dict(payload or {}),
            },
        )

    if state == EscrowState.CREATED:
        complete_in_transaction(
            session,
            key=transaction_id,
            payload=idempotency_payload,
            result_json=json.dumps(result, sort_keys=True, separators=(",", ":")),
        )
    return {"replayed": False, "result": result}


__all__ = ["cancel_escrow_in_transaction"]
