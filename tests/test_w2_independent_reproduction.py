"""Deterministic W2 reproduction vectors.

This suite intentionally reproduces the economic semantics independently of the
PostgreSQL implementation. It is not a substitute for a second deployment;
it is the deterministic semantic reproduction layer used before external
independent re-performance.
"""

from tests.oracles.w2_independent_oracle import solve_distinct_consumers, stale_decision_is_safe


def test_c2_reproduction_vector_is_deterministic():
    capacity = 2_000_000
    requests = (("A", 1_500_000), ("B", 1_500_000))
    first = solve_distinct_consumers(capacity, requests)
    second = solve_distinct_consumers(capacity, requests)

    assert first == second
    assert first.committed == (1_500_000, 0)
    assert first.over_allocated is False
    assert first.conservation_holds is True


def test_c6_reproduction_vector_rejects_changed_state():
    decision = {
        "source_account": "SRC",
        "source_balance": 2_000_000,
        "escrow_id": "ESC",
        "escrow_state": "LOCKED",
        "escrow_amount": 1_000_000,
        "requested_amount": 1_000_000,
    }
    current = {**decision, "source_balance": 500_000}

    assert stale_decision_is_safe(decision, decision) is True
    assert stale_decision_is_safe(decision, current) is False
