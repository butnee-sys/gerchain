from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from core.idempotency import IdempotencyConflictError, IdempotencyEngine


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
    """One DB transaction for idempotency, escrow, value movement and witness."""

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

            account_ids = sorted({source, destination})
            accounts = {}
            for account_id in account_ids:
                accounts[account_id] = session.execute(select(ReleaseAccount).where(ReleaseAccount.account_id == account_id).with_for_update()).scalar_one()
            if accounts[source].balance < amount:
                raise ValueError("insufficient source balance")

            accounts[source].balance -= amount
            accounts[destination].balance += amount
            escrow.state = "RELEASED"
            escrow.updated_at = now
            session.add(ReleaseWitness(transaction_id=transaction_id, event_type="RELEASED", amount=amount, created_at=now))
            op.state = "COMPLETED"
            op.result_json = "{\"state\":\"RELEASED\"}"
            op.updated_at = now
            session.commit()
            return AtomicReleaseResult(transaction_id, escrow_id, destination, amount)


def initialize_atomic_release_schema(engine) -> None:
    AtomicReleaseBase.metadata.create_all(engine)


__all__ = ["ReleaseAccount", "ReleaseEscrow", "ReleaseOperation", "ReleaseWitness", "AtomicReleaseResult", "PostgreSQLAtomicRelease", "initialize_atomic_release_schema"]
