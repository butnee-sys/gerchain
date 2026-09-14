from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.idempotency import IdempotencyConflictError, IdempotencyEngine
from persistence.recovery_outbox import OutboxEvent


class AtomicReleaseBase(DeclarativeBase):
    pass


class ReleaseAccount(AtomicReleaseBase):
    __tablename__ = "gerchain_release_accounts"
    account_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReleaseEscrow(AtomicReleaseBase):
    __tablename__ = "gerchain_release_escrows"
    escrow_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="LOCKED")
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReleaseOperation(AtomicReleaseBase):
    __tablename__ = "gerchain_release_operations"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_gerchain_release_idempotency_key"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(255), nullable=False)
    escrow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="PROCESSING")
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReleaseWitness(AtomicReleaseBase):
    __tablename__ = "gerchain_release_witnesses"
    __table_args__ = (UniqueConstraint("transaction_id", name="uq_gerchain_release_witness_transaction"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@dataclass(frozen=True)
class AtomicReleaseResult:
    transaction_id: str
    escrow_id: str
    destination: str
    amount: int
    replay: bool = False


class PostgreSQLAtomicRelease:
    """One DB transaction for release, witness and durable outbox publication."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def release(self, *, idempotency_key: str, transaction_id: str, escrow_id: str, source: str, destination: str, amount: int) -> AtomicReleaseResult:
        if not idempotency_key or not transaction_id or not escrow_id:
            raise ValueError("idempotency_key, transaction_id and escrow_id are required")
        if amount <= 0:
            raise ValueError("amount must be positive")
        payload = {"transaction_id": transaction_id, "escrow_id": escrow_id, "source": source, "destination": destination, "amount": amount}
        fingerprint = IdempotencyEngine.fingerprint(payload)
        with self.session_factory() as session:
            op = session.execute(select(ReleaseOperation).where(ReleaseOperation.idempotency_key == idempotency_key).with_for_update()).scalar_one_or_none()
            if op is not None:
                if op.fingerprint != fingerprint:
                    raise IdempotencyConflictError(f"release idempotency conflict: {idempotency_key}")
                if op.state == "COMPLETED":
                    return AtomicReleaseResult(transaction_id, escrow_id, destination, amount, replay=True)
                raise RuntimeError(f"release already processing: {idempotency_key}")

            now = datetime.now(timezone.utc)
            op = ReleaseOperation(idempotency_key=idempotency_key, fingerprint=fingerprint, transaction_id=transaction_id, escrow_id=escrow_id, destination=destination, amount=amount, state="PROCESSING", created_at=now, updated_at=now)
            session.add(op)
            session.flush()

            escrow = session.execute(select(ReleaseEscrow).where(ReleaseEscrow.escrow_id == escrow_id).with_for_update()).scalar_one()
            if escrow.state != "LOCKED":
                raise ValueError(f"escrow is not releasable: {escrow.state}")
            if escrow.amount != amount:
                raise ValueError("release amount does not match escrow amount")

            accounts = {}
            for account_id in sorted({source, destination}):
                accounts[account_id] = session.execute(select(ReleaseAccount).where(ReleaseAccount.account_id == account_id).with_for_update()).scalar_one()
            if accounts[source].balance < amount:
                raise ValueError("insufficient source balance")

            accounts[source].balance -= amount
            accounts[destination].balance += amount
            escrow.state = "RELEASED"
            escrow.updated_at = now
            session.add(ReleaseWitness(transaction_id=transaction_id, event_type="RELEASED", amount=amount, created_at=now))

            event_id = f"release:{transaction_id}"
            existing_event = session.execute(select(OutboxEvent).where(OutboxEvent.event_id == event_id).with_for_update()).scalar_one_or_none()
            if existing_event is None:
                session.add(OutboxEvent(event_id=event_id, event_type="GERCHAIN_RELEASED", aggregate_id=transaction_id, payload_json=json.dumps(payload, sort_keys=True, separators=(",", ":")), state="PENDING", lease_until=None, attempts=0, created_at=now, updated_at=now))

            op.state = "COMPLETED"
            op.result_json = json.dumps({"state": "RELEASED", "event_id": event_id}, sort_keys=True, separators=(",", ":"))
            op.updated_at = now
            session.commit()
            return AtomicReleaseResult(transaction_id, escrow_id, destination, amount)


def initialize_atomic_release_schema(engine) -> None:
    AtomicReleaseBase.metadata.create_all(engine)
    OutboxEvent.__table__.create(engine, checkfirst=True)


__all__ = ["ReleaseAccount", "ReleaseEscrow", "ReleaseOperation", "ReleaseWitness", "AtomicReleaseResult", "PostgreSQLAtomicRelease", "initialize_atomic_release_schema"]
