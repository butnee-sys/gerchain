from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class SettlementBase(DeclarativeBase):
    pass


class AccountBalance(SettlementBase):
    __tablename__ = "gerchain_account_balances"
    account_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SettlementMovement(SettlementBase):
    __tablename__ = "gerchain_settlement_movements"
    __table_args__ = (UniqueConstraint("transaction_id", name="uq_gerchain_settlement_transaction"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


@dataclass(frozen=True)
class AtomicMovementResult:
    transaction_id: str
    source: str
    destination: str
    amount: int
    replay: bool = False


class PostgreSQLAtomicSettlement:
    """Atomic DB boundary for exactly-once value movement."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def settle(self, transaction_id: str, source: str, destination: str, amount: int) -> AtomicMovementResult:
        if not transaction_id:
            raise ValueError("transaction_id is required")
        if amount <= 0:
            raise ValueError("amount must be positive")

        with self.session_factory() as session:
            existing = session.execute(
                select(SettlementMovement)
                .where(SettlementMovement.transaction_id == transaction_id)
                .with_for_update()
            ).scalar_one_or_none()
            if existing is not None:
                if existing.source != source or existing.destination != destination or existing.amount != amount:
                    raise ValueError("transaction_id already used with different settlement payload")
                session.commit()
                return AtomicMovementResult(existing.transaction_id, existing.source, existing.destination, existing.amount, replay=True)

            ordered_ids = sorted({source, destination})
            accounts = {}
            for account_id in ordered_ids:
                row = session.execute(
                    select(AccountBalance).where(AccountBalance.account_id == account_id).with_for_update()
                ).scalar_one()
                accounts[account_id] = row

            source_row = accounts[source]
            destination_row = accounts[destination]
            if source_row.balance < amount:
                raise ValueError("insufficient balance")

            source_row.balance -= amount
            destination_row.balance += amount
            now = datetime.now(timezone.utc)
            session.add(SettlementMovement(transaction_id=transaction_id, source=source, destination=destination, amount=amount, created_at=now))
            session.commit()
            return AtomicMovementResult(transaction_id, source, destination, amount, replay=False)

    def ensure_account(self, account_id: str, balance: int = 0) -> None:
        if balance < 0:
            raise ValueError("balance cannot be negative")
        with self.session_factory() as session:
            if session.get(AccountBalance, account_id) is None:
                session.add(AccountBalance(account_id=account_id, balance=balance, updated_at=datetime.now(timezone.utc)))
                session.commit()

    def get_balance(self, account_id: str) -> int:
        with self.session_factory() as session:
            row = session.get(AccountBalance, account_id)
            if row is None:
                raise ValueError(f"unknown account: {account_id}")
            return row.balance


def initialize_settlement_schema(engine) -> None:
    SettlementBase.metadata.create_all(engine)


__all__ = ["AccountBalance", "SettlementMovement", "AtomicMovementResult", "PostgreSQLAtomicSettlement", "initialize_settlement_schema"]
