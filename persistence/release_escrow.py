from __future__ import annotations

import json
from typing import Any, Mapping

from sqlalchemy.orm import Session

from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction
from persistence.durable_idempotency import get_existing_in_transaction
from persistence.escrow_aggregate import EscrowState, get_escrow


def release_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    beneficiary: str,
    amount: int,
    currency: str,
    decision_status: str,
    authorization_status: str,
    trust: bool,
    transparency: bool,
    performance: bool,
    evidence_verified: bool,
    ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Release a LOCKED escrow through the canonical Ledger boundary.

    Policy/authorization are supplied as already-evaluated evidence. This
    boundary does not create a second policy or value authority.
    """
    if amount <= 0:
        raise ValueError("release amount must be positive")
    if decision_status != "APPROVE":
        raise ValueError("release requires APPROVE decision")
    if authorization_status != "AUTHORIZED":
        raise ValueError("release requires AUTHORIZED status")
    if not all((trust, transparency, performance, evidence_verified)):
        raise ValueError("release requires complete trust evidence")

    escrow = get_escrow(session, escrow_id, for_update=False)
    idempotency_payload = {
        "escrow_id": escrow_id,
        "beneficiary": beneficiary,
        "amount": amount,
        "currency": currency,
        "decision_status": decision_status,
        "authorization_status": authorization_status,
        "trust": trust,
        "transparency": transparency,
        "performance": performance,
        "evidence_verified": evidence_verified,
        "operation": "RELEASE",
        **dict(payload or {}),
    }
    replay = get_existing_in_transaction(session, key=transaction_id, payload=idempotency_payload)
    if replay is not None:
        return {"replayed": True, "result": replay}

    escrow = get_escrow(session, escrow_id, for_update=True)
    if escrow.state != EscrowState.LOCKED.value:
        raise ValueError(f"escrow {escrow_id} must be LOCKED")
    if escrow.receiver_address != beneficiary:
        raise ValueError("release beneficiary must match authoritative escrow beneficiary")
    if int(escrow.amount) != int(amount):
        raise ValueError("release amount must match authoritative escrow amount")
    if escrow.currency and escrow.currency != currency:
        raise ValueError("release currency must match authoritative escrow currency")

    value_tx = AtomicValueTransaction(session)
    result = value_tx.transfer_and_transition(
        transaction_id=transaction_id,
        escrow_id=escrow_id,
        source=escrow_id,
        destination=beneficiary,
        amount=amount,
        currency=currency,
        expected_state=EscrowState.LOCKED,
        new_state=EscrowState.RELEASED,
        ledger_transfer=ledger_transfer,
        event_type="GERCHAIN_RELEASED",
        idempotency_payload=idempotency_payload,
        payload={
            "transaction_id": transaction_id,
            "escrow_id": escrow_id,
            "source": escrow_id,
            "destination": beneficiary,
            "amount": amount,
            "currency": currency,
            **dict(payload or {}),
        },
    )
    return {"replayed": bool(result.get("replayed")), "result": result}


__all__ = ["release_escrow_in_transaction"]
