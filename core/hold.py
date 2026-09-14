"""Hold / reservation capability for authoritative value flow.

A hold reserves an amount without moving value. It is intentionally a
capability rather than a second ledger or money engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HoldState(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class HoldError(ValueError):
    """Base error for hold operations."""


class HoldNotFoundError(HoldError):
    pass


class HoldConflictError(HoldError):
    pass


@dataclass(frozen=True)
class Hold:
    hold_id: str
    account_id: str
    amount: int
    currency: str
    state: HoldState = HoldState.ACTIVE
    reference: str | None = None


class HoldEngine:
    """In-memory authoritative reservation capability for one runtime."""

    def __init__(self) -> None:
        self._holds: dict[str, Hold] = {}

    def create(
        self,
        *,
        hold_id: str,
        account_id: str,
        amount: int,
        currency: str,
        available_balance: int,
        reference: str | None = None,
    ) -> Hold:
        if not hold_id or not account_id or not currency:
            raise ValueError("hold_id, account_id and currency are required")
        if amount <= 0:
            raise ValueError("hold amount must be positive")
        if available_balance < amount:
            raise HoldConflictError("insufficient available balance")
        if hold_id in self._holds:
            raise HoldConflictError(f"hold already exists: {hold_id}")

        hold = Hold(
            hold_id=hold_id,
            account_id=account_id,
            amount=amount,
            currency=currency,
            reference=reference,
        )
        self._holds[hold_id] = hold
        return hold

    def get(self, hold_id: str) -> Hold:
        try:
            return self._holds[hold_id]
        except KeyError as exc:
            raise HoldNotFoundError(f"hold not found: {hold_id}") from exc

    def release(self, hold_id: str) -> Hold:
        hold = self.get(hold_id)
        if hold.state != HoldState.ACTIVE:
            raise HoldConflictError("only an active hold can be released")
        updated = Hold(**{**hold.__dict__, "state": HoldState.RELEASED})
        self._holds[hold_id] = updated
        return updated

    def cancel(self, hold_id: str) -> Hold:
        hold = self.get(hold_id)
        if hold.state != HoldState.ACTIVE:
            raise HoldConflictError("only an active hold can be cancelled")
        updated = Hold(**{**hold.__dict__, "state": HoldState.CANCELLED})
        self._holds[hold_id] = updated
        return updated

    def reserved(self, account_id: str) -> int:
        return sum(
            hold.amount
            for hold in self._holds.values()
            if hold.account_id == account_id and hold.state == HoldState.ACTIVE
        )

    def available(self, account_id: str, balance: int) -> int:
        return balance - self.reserved(account_id)


__all__ = ["Hold", "HoldConflictError", "HoldEngine", "HoldError", "HoldNotFoundError", "HoldState"]
