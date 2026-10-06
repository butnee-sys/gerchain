from __future__ import annotations

import json
from typing import Any, Mapping

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction
from persistence.durable_idempotency import (
    begin_in_transaction,
    complete_in_transaction,
    get_existing_in_transaction,
)
from persistence.escrow_aggregate import EscrowState


def cancel_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Cancel CREATED/FUNDED escrow with one durable idempotency boundary."""
    from sqlalchemy import select
    from persistence.atomic_ledger import LedgerMovementModel
    from persistence.escrow_aggregate import CanonicalEscrow, transition_escrow

    escrow = session.execute(
        select(CanonicalEscrow)
        .where(CanonicalEscrow.id == escrow_id)
        .with_for_update()
    ).scalar_one()

    state = EscrowState(escrow.state)
    if state not in (EscrowState.CREATED, EscrowState.FUNDED):
        movement = session.execute(
            select(LedgerMovementModel)
            .where(LedgerMovementModel.transaction_id == transaction_id)
        ).scalar_one_or_none()
        original_state = EscrowState.FUNDED if movement is not None else EscrowState.CREATED
        original_destination = escrow.sender_address if original_state == EscrowState.FUNDED else None
        original_amount = int(escrow.amount) if original_state == EscrowState.FUNDED else 0
        replay_payload = {
            "escrow_id": escrow_id,
            "operation": "CANCEL",
            "state": original_state.value,
            "source": escrow_id if original_state == EscrowState.FUNDED else None,
            "destination": original_destination,
            "amount": original_amount,
            "currency": escrow.currency,
            **dict(payload or {}),
        }
        replay = get_existing_in_transaction(session, key=transaction_id, payload=replay_payload)
        if replay is not None:
            return {"replayed": True, "result": replay}
        raise ValueError(f"escrow {escrow_id} cannot be cancelled from {state.value}")

    destination = escrow.sender_address if state == EscrowState.FUNDED else None
    amount = int(escrow.amount) if state == EscrowState.FUNDED else 0
    idempotency_payload = {
        "escrow_id": escrow_id,
        "operation": "CANCEL",
        "state": state.value,
        "source": escrow_id if state == EscrowState.FUNDED else None,
        "destination": destination,
        "amount": amount,
        "currency": escrow.currency,
        **dict(payload or {}),
    }

    replay = get_existing_in_transaction(
        session, key=transaction_id, payload=idempotency_payload
    )
    if replay is not None:
        return {"replayed": True, "result": replay}

    if state == EscrowState.CREATED:
        begin_in_transaction(
            session, key=transaction_id, payload=idempotency_payload
        )
        transition_escrow(
            session, escrow_id, EscrowState.CREATED, EscrowState.CANCELLED
        )
        result = {"status": "CANCELLED", "value_movement": False, "amount": 0}
        complete_in_transaction(
            session,
            key=transaction_id,
            payload=idempotency_payload,
            result_json=json.dumps(result, sort_keys=True, separators=(",", ":")),
        )
        return {"replayed": False, "result": result}

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
    if result.get("replayed") is True:
        return result
    return {"replayed": False, "result": result}


__all__ = ["cancel_escrow_in_transaction"]
