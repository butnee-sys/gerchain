from __future__ import annotations

from datetime import datetime, timezone
import json
import hashlib
from enum import StrEnum
from typing import Mapping

from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from persistence.escrow_aggregate import EscrowState, transition_escrow
from persistence.transactional_outbox import deterministic_event_id, enqueue_in_transaction
from persistence.durable_idempotency import begin_in_transaction, complete_in_transaction


class WitnessBase(DeclarativeBase):
    pass


class TransactionWitness(WitnessBase):
    """Durable execution evidence; not a second witness chain."""

    __tablename__ = "gerchain_transaction_witnesses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    escrow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def record_witness_in_transaction(
    session: Session,
    *,
    transaction_id: str,
    event_type: str,
    escrow_id: str,
    amount: int,
) -> bool:
    existing = session.execute(
        select(TransactionWitness)
        .where(TransactionWitness.transaction_id == transaction_id)
        .with_for_update()
    ).scalar_one_or_none()
    if existing is not None:
        if (existing.event_type, existing.escrow_id, existing.amount) != (
            event_type,
            escrow_id,
            amount,
        ):
            raise ValueError("transaction witness conflict")
        return False

    session.add(
        TransactionWitness(
            transaction_id=transaction_id,
            event_type=event_type,
            escrow_id=escrow_id,
            amount=amount,
            created_at=datetime.now(timezone.utc),
        )
    )
    return True


class AtomicValueTransaction:
    """Small orchestration boundary for Ledger + Escrow + Witness + Outbox.

    It deliberately does not decide policy, authorization or value ownership.
    Those remain outside this coordinator.
    """

    def __init__(self, session: Session):
        self.session = session

    def transfer_and_transition(
        self,
        *,
        transaction_id: str,
        escrow_id: str,
        source: str,
        destination: str,
        amount: int,
        currency: str,
        expected_state: EscrowState,
        new_state: EscrowState,
        ledger_transfer,
        event_type: str,
        payload: Mapping[str, object],
        idempotency_payload: Mapping[str, object] | None = None,
    ) -> dict:
        idempotency_payload = dict(idempotency_payload or {
            "escrow_id": escrow_id,
            "source": source,
            "destination": destination,
            "amount": amount,
            "currency": currency,
            "expected_state": expected_state.value,
            "new_state": new_state.value,
            "event_type": event_type,
        })
        replay = begin_in_transaction(
            self.session,
            key=transaction_id,
            payload=idempotency_payload,
        )
        if replay is not None:
            return {"replayed": True, "result": replay}

        operation = {
            "GERCHAIN_FUNDED": "FUND",
            "GERCHAIN_RELEASED": "RELEASE",
            "GERCHAIN_REFUNDED": "REFUND",
            "GERCHAIN_CANCELLED": "CANCEL",
            "GERCHAIN_SETTLED": "SETTLEMENT",
        }.get(event_type)
        if operation is None:
            raise ValueError(f"unsupported value event type: {event_type}")
        integrity_material = json.dumps(
            {
                "transaction_id": transaction_id,
                "operation": operation,
                "escrow_id": escrow_id,
                "source": source,
                "destination": destination,
                "amount": amount,
                "currency": currency,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        integrity_hash = hashlib.sha256(integrity_material.encode("utf-8")).hexdigest()
        result = ledger_transfer(
            self.session,
            transaction_id,
            source,
            destination,
            amount,
            currency,
            operation,
            escrow_id,
            integrity_hash,
        )
        transition_escrow(
            self.session,
            escrow_id,
            expected_state,
            new_state,
        )
        record_witness_in_transaction(
            self.session,
            transaction_id=transaction_id,
            event_type=event_type,
            escrow_id=escrow_id,
            amount=amount,
        )
        enqueue_in_transaction(
            self.session,
            event_id=deterministic_event_id(event_type, transaction_id),
            event_type=event_type,
            aggregate_id=escrow_id,
            payload=dict(payload),
        )
        complete_in_transaction(
            self.session,
            key=transaction_id,
            payload=idempotency_payload,
            result_json=json.dumps(result, sort_keys=True, separators=(",", ":")),
        )
        return result


__all__ = [
    "TransactionWitness",
    "record_witness_in_transaction",
    "AtomicValueTransaction",
]
