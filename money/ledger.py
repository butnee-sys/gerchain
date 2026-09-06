"""
GerChain V78.0
Digital money ledger.

Purpose:
- Deterministic balance tracking.
- Every monetary movement has an explicit source and destination.
- Negative balances are rejected.
- Settlement logic is separated from escrow state logic.
"""

from __future__ import annotations

from typing import Dict


class MoneyLedger:
    """Эскроу мөнгөний үлдэгдлийг детерминистик хөтлөгч."""

    def __init__(self, currency: str):
        self.currency = currency
        self.balances: Dict[str, int] = {}

    def create_account(
        self,
        account_id: str,
        initial_balance: int = 0,
    ) -> None:
        if initial_balance < 0:
            raise ValueError(
                "Initial balance cannot be negative."
            )

        if account_id in self.balances:
            raise ValueError(
                f"Account already exists: {account_id}"
            )

        self.balances[account_id] = initial_balance

    def get_balance(self, account_id: str) -> int:
        if account_id not in self.balances:
            raise ValueError(
                f"Unknown account: {account_id}"
            )

        return self.balances[account_id]

    def transfer(
        self,
        source: str,
        destination: str,
        amount: int,
    ) -> None:
        if amount <= 0:
            raise ValueError(
                "Transfer amount must be positive."
            )

        if source not in self.balances:
            raise ValueError(
                f"Unknown source account: {source}"
            )

        if destination not in self.balances:
            raise ValueError(
                f"Unknown destination account: {destination}"
            )

        if self.balances[source] < amount:
            raise ValueError(
                "Insufficient balance."
            )

        self.balances[source] -= amount
        self.balances[destination] += amount


__all__ = [
    "MoneyLedger",
]