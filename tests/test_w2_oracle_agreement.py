from tests.oracles.w2_independent_oracle import solve_distinct_consumers, stale_decision_is_safe


def test_c2_oracle_expected_result_is_one_commit():
    result = solve_distinct_consumers(capacity=2_000_000, requests=(1_500_000, 1_500_000))
    assert sum(result.committed) == 1_500_000
    assert result.committed[0] + result.committed[1] <= result.capacity


def test_c6_oracle_requires_exact_relevant_state_match():
    state = {"source_balance": 2_000_000, "escrow_state": "LOCKED", "escrow_amount": 1_000_000}
    changed = {"source_balance": 1_000_000, "escrow_state": "LOCKED", "escrow_amount": 1_000_000}
    assert stale_decision_is_safe(decision_state=state, current_state=state)
    assert not stale_decision_is_safe(decision_state=state, current_state=changed)
