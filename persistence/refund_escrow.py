from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction
from persistence.durable_idempotency import get_existing_in_transaction
from persistence.escrow_aggregate import EscrowState, transition_escrow


def refund_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    amount: int,
    currency: str,
    ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Refund a LOCKED escrow only to its authoritative refund destination."""
    if amount <= 0:
        raise ValueError("refund amount must be positive")

    from sqlalchemy import select
    from persistence.escrow_aggregate import CanonicalEscrow

    escrow = session.execute(
        select(CanonicalEscrow).where(CanonicalEscrow.id == escrow_id)
    ).scalar_one()

    if escrow.currency != currency:
        raise ValueError("refund currency does not match escrow currency")
    if int(escrow.amount) != amount:
        raise ValueError("refund amount does not match escrow amount")
    if not escrow.refund_destination:
        raise ValueError("authoritative refund destination is required")

    destination = escrow.refund_destination
    idempotency_payload = {
        "escrow_id": escrow_id,
        "source": escrow_id,
        "destination": destination,
        "amount": amount,
        "currency": currency,
        "operation": "REFUND",
        **dict(payload or {}),
    }

    replay = get_existing_in_transaction(session, key=transaction_id, payload=idempotency_payload)
    if replay is not None:
        return {"replayed": True, "result": replay}

    escrow = session.execute(
        select(CanonicalEscrow).where(CanonicalEscrow.id == escrow_id).with_for_update()
    ).scalar_one()
    result = AtomicValueTransaction(session).transfer_and_transition(
        transaction_id=transaction_id,
        escrow_id=escrow_id,
        source=escrow_id,
        destination=destination,
        amount=amount,
        currency=currency,
        expected_state=EscrowState.LOCKED,
        new_state=EscrowState.REFUNDED,
        ledger_transfer=ledger_transfer,
        event_type="GERCHAIN_REFUNDED",
        idempotency_payload=idempotency_payload,
        payload={
            "transaction_id": transaction_id,
            "escrow_id": escrow_id,
            "source": escrow_id,
            "destination": destination,
            "amount": amount,
            "currency": currency,
            **dict(payload or {}),
        },
    )
    return {"replayed": bool(result.get("replayed")), "result": result}


__all__ = ["refund_escrow_in_transaction"]
