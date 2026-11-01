from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from dee_security.root_of_trust import RootOfTrust, SecurityError, SignedChange
from persistence.atomic_ledger import PostgreSQLAtomicLedger
from persistence.atomic_value_transaction import AtomicValueTransaction
from persistence.durable_idempotency import get_existing_in_transaction
from persistence.escrow_aggregate import EscrowState, get_escrow
from persistence.signed_change_authorization import (
    canonical_release_payload,
    consume_signed_change_in_transaction,
    require_pinned_root,
    verify_signed_change,
)


def release_escrow_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    escrow_id: str,
    beneficiary: str,
    amount: int,
    currency: str,
    decision_status: str,
    root: RootOfTrust,
    signed_change: SignedChange,
    owner_id: str,
    trust: bool,
    transparency: bool,
    performance: bool,
    evidence_verified: bool,
    ledger_transfer=PostgreSQLAtomicLedger.transfer_in_transaction,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Release a LOCKED escrow only after consuming a deployment-pinned SignedChange.

    The authorization record, ledger movement, escrow transition, witness,
    outbox event, and idempotency completion share the caller's DB transaction.
    """
    if not isinstance(root, RootOfTrust) or not isinstance(signed_change, SignedChange):
        raise SecurityError("RootOfTrust and SignedChange are mandatory for RELEASE")
    if not transaction_id or not escrow_id or not beneficiary or not owner_id:
        raise ValueError("RELEASE transaction, escrow, beneficiary and owner are required")
    if amount <= 0:
        raise ValueError("release amount must be positive")
    if decision_status != "APPROVE":
        raise ValueError("release requires APPROVE decision")
    if not all((trust, transparency, performance, evidence_verified)):
        raise ValueError("release requires complete trust evidence")

    request_payload = dict(payload or {})
    authorization_payload = canonical_release_payload(
        transaction_id=transaction_id,
        escrow_id=escrow_id,
        source=escrow_id,
        destination=beneficiary,
        amount=amount,
        currency=currency,
        decision_status=decision_status,
        trust=trust,
        transparency=transparency,
        performance=performance,
        evidence_verified=evidence_verified,
        evidence=request_payload.get("evidence"),
    )
    # Verify even an idempotent retry; a stored result must not become a way to
    # bypass the current caller's signature and deployment-pinned trust anchor.
    pinned_root = require_pinned_root(root)
    authorization_digest = verify_signed_change(
        root=pinned_root,
        signed_change=signed_change,
        owner_id=owner_id,
        expected_payload=authorization_payload,
    )

    escrow = get_escrow(session, escrow_id, for_update=False)
    idempotency_payload = {
        **request_payload,
        "escrow_id": escrow_id,
        "beneficiary": beneficiary,
        "amount": amount,
        "currency": currency,
        "decision_status": decision_status,
        "trust": trust,
        "transparency": transparency,
        "performance": performance,
        "evidence_verified": evidence_verified,
        "operation": "RELEASE",
        "authorization_change_id": signed_change.change_id,
        "authorization_payload_hash": authorization_digest,
        "authorization_owner_id": owner_id,
    }
    replay = get_existing_in_transaction(
        session,
        key=transaction_id,
        payload=idempotency_payload,
    )
    if replay is not None:
        return {"replayed": True, "result": replay}

    consume_signed_change_in_transaction(
        session,
        root=pinned_root,
        signed_change=signed_change,
        owner_id=owner_id,
        operation="RELEASE",
        transaction_id=transaction_id,
        escrow_id=escrow_id,
        expected_payload=authorization_payload,
    )

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
            **request_payload,
            "transaction_id": transaction_id,
            "escrow_id": escrow_id,
            "source": escrow_id,
            "destination": beneficiary,
            "amount": amount,
            "currency": currency,
        },
    )
    return {"replayed": bool(result.get("replayed")), "result": result}


__all__ = ["release_escrow_in_transaction"]
