from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState


def fund_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    source: str,
    amount: int,
    currency: str,
    ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fund a CREATED escrow through the Canonical Ledger boundary."""
    if not transaction_id:
        raise ValueError("transaction_id is required")
    if not source:
        raise ValueError("source is required")
    if amount <= 0:
        raise ValueError("fund amount must be positive")

    escrow = session.execute(
        select(CanonicalEscrow)
        .where(CanonicalEscrow.id == escrow_id)
        .with_for_update()
    ).scalar_one()

    if escrow.currency != currency:
        raise ValueError("fund currency does not match escrow currency")
    if int(escrow.amount) != amount:
        raise ValueError("fund amount does not match escrow amount")

    idempotency_payload = {
        "escrow_id": escrow_id,
        "operation": "FUND",
        "source": source,
        "destination": escrow_id,
        "amount": amount,
        "currency": currency,
        **dict(payload or {}),
    }

    return AtomicValueTransaction(session).transfer_and_transition(
        transaction_id=transaction_id,
        escrow_id=escrow_id,
        source=source,
        destination=escrow_id,
        amount=amount,
        currency=currency,
        expected_state=EscrowState.CREATED,
        new_state=EscrowState.FUNDED,
        ledger_transfer=ledger_transfer,
        event_type="GERCHAIN_FUNDED",
        idempotency_payload=idempotency_payload,
        payload={
            "transaction_id": transaction_id,
            "escrow_id": escrow_id,
            "source": source,
            "destination": escrow_id,
            "amount": amount,
            "currency": currency,
            **dict(payload or {}),
        },
    )


__all__ = ["fund_escrow_in_transaction"]
