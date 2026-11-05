from __future__ import annotations

from typing import Any, Mapping

from dee_security.root_of_trust import RootOfTrust, SecurityError, SignedChange
from sqlalchemy import select
from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction
from persistence.durable_idempotency import get_existing_in_transaction
from persistence.escrow_aggregate import CanonicalEscrow, EscrowState
from persistence.signed_change_authorization import (
    canonical_refund_payload,
    consume_signed_change_in_transaction,
    require_pinned_root,
    verify_signed_change,
)


def refund_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    amount: int,
    currency: str,
    root: RootOfTrust,
    signed_change: SignedChange,
    owner_id: str,
    authorized: bool,
    transparency: bool,
    dispute_or_cancellation_verified: bool,
    ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Refund only a LOCKED escrow after consuming its signed REFUND approval."""
    if not transaction_id or not escrow_id or not owner_id:
        raise ValueError("REFUND transaction, escrow and owner identifiers are required")
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("refund amount must be a positive integer")
    if authorized is not True:
        raise SecurityError("REFUND requires authorized approval")
    if transparency is not True:
        raise SecurityError("REFUND requires transparent evidence")
    if dispute_or_cancellation_verified is not True:
        raise SecurityError("REFUND requires verified dispute or cancellation evidence")

    request_payload = dict(payload or {})
    # Lock before reading state or deriving the authoritative destination. This
    # serializes concurrent RELEASE/REFUND attempts on PostgreSQL.
    escrow = session.execute(
        select(CanonicalEscrow)
        .where(CanonicalEscrow.id == escrow_id)
        .with_for_update()
    ).scalar_one()

    if escrow.currency != currency:
        raise ValueError("refund currency does not match escrow currency")
    if int(escrow.amount) != amount:
        raise ValueError("refund amount does not match escrow amount")
    if not escrow.refund_destination:
        raise ValueError("authoritative refund destination is required")

    destination = escrow.refund_destination
    authorization_payload = canonical_refund_payload(
        transaction_id=transaction_id,
        escrow_id=escrow_id,
        source=escrow_id,
        destination=destination,
        amount=amount,
        currency=currency,
        authorized=authorized,
        transparency=transparency,
        dispute_or_cancellation_verified=dispute_or_cancellation_verified,
        evidence=request_payload.get("evidence"),
    )
    pinned_root = require_pinned_root(root)
    authorization_digest = verify_signed_change(
        root=pinned_root,
        signed_change=signed_change,
        owner_id=owner_id,
        expected_payload=authorization_payload,
    )

    idempotency_payload = {
        **request_payload,
        "escrow_id": escrow_id,
        "source": escrow_id,
        "destination": destination,
        "amount": amount,
        "currency": currency,
        "operation": "REFUND",
        "authorized": True,
        "transparency": True,
        "dispute_or_cancellation_verified": True,
        "authorization_change_id": signed_change.change_id,
        "authorization_payload_hash": authorization_digest,
        "authorization_owner_id": owner_id,
    }
    replay = get_existing_in_transaction(
        session, key=transaction_id, payload=idempotency_payload
    )
    if replay is not None:
        return {"replayed": True, "result": replay}

    # LOCKED excludes RELEASED, REFUNDED and all other states. The explicit
    # check is retained even though the aggregate transition also enforces it.
    if escrow.state != EscrowState.LOCKED.value:
        raise ValueError(
            f"REFUND requires LOCKED escrow; got {escrow.state}"
        )

    consume_signed_change_in_transaction(
        session,
        root=pinned_root,
        signed_change=signed_change,
        owner_id=owner_id,
        operation="REFUND",
        transaction_id=transaction_id,
        escrow_id=escrow_id,
        expected_payload=authorization_payload,
    )

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
            **request_payload,
            "transaction_id": transaction_id,
            "escrow_id": escrow_id,
            "source": escrow_id,
            "destination": destination,
            "amount": amount,
            "currency": currency,
            "operation": "REFUND",
            "authorization_change_id": signed_change.change_id,
            "authorization_payload_hash": authorization_digest,
        },
    )
    return {"replayed": bool(result.get("replayed")), "result": result}


__all__ = ["refund_escrow_in_transaction"]
