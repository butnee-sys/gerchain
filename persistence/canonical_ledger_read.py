from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from persistence.atomic_ledger import LedgerAccountModel


class CanonicalLedgerRead:
    """Production balance-read boundary backed only by Canonical Ledger."""

    def __init__(self, session: Session):
        self.session = session

    def get_balance(self, account_id: str, currency: str | None = None) -> int:
        row = self.session.get(LedgerAccountModel, account_id)
        if row is None:
            raise ValueError(f"unknown canonical ledger account: {account_id}")
        if currency is not None and row.currency != currency:
            raise ValueError("currency mismatch")
        return int(row.balance)

    def get_account(self, account_id: str) -> dict[str, Any]:
        row = self.session.get(LedgerAccountModel, account_id)
        if row is None:
            raise ValueError(f"unknown canonical ledger account: {account_id}")
        return {
            "account_id": row.account_id,
            "currency": row.currency,
            "balance": int(row.balance),
            "version": int(row.version),
            "updated_at": row.updated_at,
        }


__all__ = ["CanonicalLedgerRead"]
