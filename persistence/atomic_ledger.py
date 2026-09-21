from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class AtomicLedgerBase(DeclarativeBase):
    pass


class LedgerAccountModel(AtomicLedgerBase):
    __tablename__ = "gerchain_ledger_accounts"

    account_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LedgerMovementModel(AtomicLedgerBase):
    __tablename__ = "gerchain_ledger_movements"
    __table_args__ = (UniqueConstraint("transaction_id", name="uq_gerchain_ledger_transaction"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    destination: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PostgreSQLAtomicLedger:
    """Database-authoritative monetary movement and account boundary."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    @staticmethod
    def create_account_in_transaction(
        session: Session,
        account_id: str,
        currency: str,
        initial_balance: int = 0,
    ) -> dict[str, Any]:
        if not account_id:
            raise ValueError("account_id is required")
        if not currency:
            raise ValueError("currency is required")
        if initial_balance < 0:
            raise ValueError("initial_balance cannot be negative")

        existing = session.execute(
            select(LedgerAccountModel)
            .where(LedgerAccountModel.account_id == account_id)
            .with_for_update()
        ).scalar_one_or_none()
        if existing is not None:
            if existing.currency != currency or existing.balance != initial_balance:
                raise ValueError("Account already exists with different canonical state")
            return {"account_id": account_id, "currency": currency, "balance": int(existing.balance), "version": int(existing.version), "replayed": True}

        now = datetime.now(timezone.utc)
        session.add(LedgerAccountModel(
            account_id=account_id,
            currency=currency,
            balance=initial_balance,
            version=0,
            updated_at=now,
        ))
        return {"account_id": account_id, "currency": currency, "balance": initial_balance, "version": 0, "replayed": False}

    def create_account(self, account_id: str, currency: str, initial_balance: int = 0) -> dict[str, Any]:
        with self.session_factory() as session:
            result = self.create_account_in_transaction(session, account_id, currency, initial_balance)
            session.commit()
            return result

    @staticmethod
    def transfer_in_transaction(
        session: Session,
        transaction_id: str,
        source: str,
        destination: str,
        amount: int,
        currency: str,
    ) -> dict[str, Any]:
        if not transaction_id:
            raise ValueError("transaction_id is required")
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        if source == destination:
            raise ValueError("Source and destination must differ")

        existing = session.execute(
            select(LedgerMovementModel)
            .where(LedgerMovementModel.transaction_id == transaction_id)
            .with_for_update()
        ).scalar_one_or_none()
        if existing is not None:
            if (existing.source, existing.destination, existing.amount, existing.currency) != (source, destination, amount, currency):
                raise ValueError("Transaction ID was reused with different movement")
            return {"transaction_id": transaction_id, "source": source, "destination": destination, "amount": amount, "currency": currency, "replayed": True}

        first, second = sorted((source, destination))
        first_row = session.execute(select(LedgerAccountModel).where(LedgerAccountModel.account_id == first).with_for_update()).scalar_one()
        second_row = session.execute(select(LedgerAccountModel).where(LedgerAccountModel.account_id == second).with_for_update()).scalar_one()
        source_row = first_row if first == source else second_row
        destination_row = first_row if first == destination else second_row

        if source_row.currency != currency or destination_row.currency != currency:
            raise ValueError("Currency mismatch")
        if source_row.balance < amount:
            raise ValueError("Insufficient balance")

        now = datetime.now(timezone.utc)
        source_row.balance -= amount
        source_row.version += 1
        source_row.updated_at = now
        destination_row.balance += amount
        destination_row.version += 1
        destination_row.updated_at = now
        session.add(LedgerMovementModel(transaction_id=transaction_id, source=source, destination=destination, amount=amount, currency=currency, created_at=now))
        return {"transaction_id": transaction_id, "source": source, "destination": destination, "amount": amount, "currency": currency, "replayed": False}

    def transfer(self, transaction_id: str, source: str, destination: str, amount: int, currency: str) -> dict[str, Any]:
        with self.session_factory() as session:
            result = self.transfer_in_transaction(session, transaction_id, source, destination, amount, currency)
            session.commit()
            return result


__all__ = ["LedgerAccountModel", "LedgerMovementModel", "PostgreSQLAtomicLedger"]
