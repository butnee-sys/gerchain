"""Independent W2 semantic re-performance implementation.

This module intentionally has zero imports from GerChain production code,
including persistence, CORE fingerprints, and release services. It implements
only the W2 economic semantics from the contract so that an independent
executor can run the vectors in a separate Python environment.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class IndependentLiquidityResult:
    committed: tuple[int, ...]
    capacity: int

    @property
    def committed_total(self) -> int:
        return sum(self.committed)

    @property
    def over_allocated(self) -> bool:
        return self.committed_total > self.capacity

    @property
    def conservation_holds(self) -> bool:
        return self.committed_total <= self.capacity


def independently_resolve_distinct_requests(
    *, capacity: int, requests: tuple[int, ...]
) -> IndependentLiquidityResult:
    """Resolve distinct consumers without importing production semantics."""
    remaining = capacity
    committed: list[int] = []
    for amount in requests:
        if amount <= 0:
            raise ValueError("request amount must be positive")
        if amount <= remaining:
            committed.append(amount)
            remaining -= amount
        else:
            committed.append(0)
    return IndependentLiquidityResult(tuple(committed), capacity)


def independent_state_digest(state: dict) -> str:
    canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def independently_accept_decision(*, decision_state: dict, current_state: dict) -> bool:
    """A decision is admissible only when the complete relevant state agrees."""
    return independent_state_digest(decision_state) == independent_state_digest(current_state)


if __name__ == "__main__":
    result = independently_resolve_distinct_requests(
        capacity=2_000_000,
        requests=(1_500_000, 1_500_000),
    )
    if result.committed_total != 1_500_000 or result.over_allocated or not result.conservation_holds:
        raise SystemExit("W2 C2 independent re-performance FAILED")

    state = {
        "source_account": "A",
        "source_balance": 2_000_000,
        "escrow_id": "E",
        "escrow_state": "LOCKED",
        "escrow_amount": 1_000_000,
        "requested_amount": 1_000_000,
    }
    changed = dict(state, source_balance=500_000)
    if not independently_accept_decision(decision_state=state, current_state=changed):
        pass
    else:
        raise SystemExit("W2 C6 independent re-performance FAILED")

    print("W2 independent semantic re-performance: PASS")
