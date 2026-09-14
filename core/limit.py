"""Rule-based value-flow limits.

Limits constrain permitted exposure; they do not move money and do not own
ledger state.
"""

from __future__ import annotations

from dataclasses import dataclass


class LimitExceededError(ValueError):
    """Raised when a requested amount exceeds a configured limit."""


@dataclass(frozen=True)
class LimitRule:
    limit_id: str
    subject_id: str
    currency: str
    max_amount: int
    cumulative: bool = False

    def check(self, amount: int, current_amount: int = 0) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        if current_amount < 0:
            raise ValueError("current_amount cannot be negative")
        effective = current_amount + amount if self.cumulative else amount
        if effective > self.max_amount:
            raise LimitExceededError(
                f"limit exceeded: {self.limit_id} ({effective} > {self.max_amount})"
            )


class LimitEngine:
    """Authoritative policy capability for one runtime."""

    def __init__(self) -> None:
        self._rules: dict[str, LimitRule] = {}

    def add(self, rule: LimitRule) -> None:
        if rule.max_amount <= 0:
            raise ValueError("max_amount must be positive")
        if rule.limit_id in self._rules:
            raise ValueError(f"limit already exists: {rule.limit_id}")
        self._rules[rule.limit_id] = rule

    def get(self, limit_id: str) -> LimitRule:
        try:
            return self._rules[limit_id]
        except KeyError as exc:
            raise ValueError(f"limit not found: {limit_id}") from exc

    def check(
        self,
        *,
        limit_id: str,
        amount: int,
        current_amount: int = 0,
    ) -> None:
        self.get(limit_id).check(amount, current_amount)


__all__ = ["LimitEngine", "LimitExceededError", "LimitRule"]
