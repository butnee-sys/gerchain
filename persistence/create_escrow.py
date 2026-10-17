from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.escrow_aggregate import CanonicalEscrow, EscrowState


def create_escrow_in_transaction(
    session: Session,
    *,
    escrow_id: str,
    source: str,
    beneficiary: str,
    refund_destination: str,
    amount: int,
    currency: str,
    condition: str | None = None,
) -> dict[str, Any]:
    """Create the single durable canonical escrow aggregate.

    CREATE establishes escrow truth only; it never moves value.
    Repeating the same request is idempotent. Reusing an ID with different
    canonical fields is rejected.
    """
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

    existing = session.execute(
        select(CanonicalEscrow)
        .where(CanonicalEscrow.id == escrow_id)
        .with_for_update()
    ).scalar_one_or_none()

    if existing is not None:
        same = (
            existing.sender_address == source
            and existing.receiver_address == beneficiary
            and existing.refund_destination == refund_destination
            and int(existing.amount) == amount
            and existing.currency == currency
            and existing.condition_desc == condition
            and existing.state == EscrowState.CREATED.value
        )
        if not same:
            raise ValueError("escrow ID reused with different canonical state")
        return {
            "escrow_id": escrow_id,
            "state": existing.state,
            "amount": int(existing.amount),
            "currency": existing.currency,
            "version": int(existing.version),
            "replayed": True,
        }

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
    return {
        "escrow_id": escrow_id,
        "state": EscrowState.CREATED.value,
        "amount": amount,
        "currency": currency,
        "version": 0,
        "replayed": False,
    }


def create_escrow(
    session_factory,
    **kwargs: Any,
) -> dict[str, Any]:
    with session_factory() as session:
        result = create_escrow_in_transaction(session, **kwargs)
        session.commit()
        return result


__all__ = ["create_escrow_in_transaction", "create_escrow"]
