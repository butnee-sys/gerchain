from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction
from persistence.escrow_aggregate import EscrowState


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
    """Atomically fund a CREATED escrow from the funding source.

    The escrow aggregate itself is the destination ledger account for the
    funding movement. No second value store is introduced.
    """
    if amount <= 0:
        raise ValueError("funding amount must be positive")

    value_tx = AtomicValueTransaction(session)
    return value_tx.transfer_and_transition(
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
