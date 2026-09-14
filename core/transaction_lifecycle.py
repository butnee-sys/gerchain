"""Deterministic transaction lifecycle and state-machine capability.

This module governs transaction state transitions only. It does not move
value, authorize release, or replace the ledger/escrow engines.
"""

from __future__ import annotations

from enum import Enum


class TransactionState(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REVERSED = "REVERSED"
    FINAL = "FINAL"


class InvalidTransitionError(ValueError):
    pass


_TRANSITIONS: dict[TransactionState, frozenset[TransactionState]] = {
    TransactionState.CREATED: frozenset({TransactionState.PENDING, TransactionState.CANCELLED}),
    TransactionState.PENDING: frozenset({TransactionState.ACTIVE, TransactionState.FAILED, TransactionState.CANCELLED}),
    TransactionState.ACTIVE: frozenset({TransactionState.LOCKED, TransactionState.FAILED, TransactionState.CANCELLED}),
    TransactionState.LOCKED: frozenset({TransactionState.PROCESSING, TransactionState.CANCELLED}),
    TransactionState.PROCESSING: frozenset({TransactionState.COMPLETED, TransactionState.FAILED}),
    TransactionState.COMPLETED: frozenset({TransactionState.FINAL, TransactionState.REVERSED}),
    TransactionState.FAILED: frozenset({TransactionState.PENDING, TransactionState.CANCELLED}),
    TransactionState.CANCELLED: frozenset(),
    TransactionState.REVERSED: frozenset({TransactionState.FINAL}),
    TransactionState.FINAL: frozenset(),
}


class TransactionStateMachine:
    """Fail-closed deterministic transaction transition capability."""

    def __init__(self, initial: TransactionState = TransactionState.CREATED) -> None:
        self._state = initial

    @property
    def state(self) -> TransactionState:
        return self._state

    def can_transition(self, target: TransactionState) -> bool:
        return target in _TRANSITIONS[self._state]

    def transition(self, target: TransactionState) -> TransactionState:
        if not self.can_transition(target):
            raise InvalidTransitionError(
                f"invalid transaction transition: {self._state.value} -> {target.value}"
            )
        self._state = target
        return self._state


__all__ = ["InvalidTransitionError", "TransactionState", "TransactionStateMachine"]
