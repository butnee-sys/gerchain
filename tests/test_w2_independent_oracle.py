from tests.oracles.w2_independent_oracle import solve_distinct_consumers, stale_decision_is_safe


def test_oracle_never_over_allocates_shared_liquidity():
    result = solve_distinct_consumers(capacity=2_000_000, requests=(1_500_000, 1_500_000))
    assert result.committed == (1_500_000, 0)
    assert result.conservation_holds
    assert not result.over_allocated


def test_oracle_rejects_changed_decision_state():
    decision = {"balance": 2_000_000, "escrow_state": "LOCKED"}
    current = {"balance": 500_000, "escrow_state": "LOCKED"}
    assert not stale_decision_is_safe(decision_state=decision, current_state=current)
