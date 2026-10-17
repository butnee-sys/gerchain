from core.economic_state import fingerprint_relevant_state, state_matches


def test_same_relevant_state_has_same_identity() -> None:
    a = fingerprint_relevant_state(
        version="liquidity:1",
        state={"capacity": 2_000_000, "reserved": 0, "consumed": 0},
    )
    b = fingerprint_relevant_state(
        version="liquidity:1",
        state={"consumed": 0, "reserved": 0, "capacity": 2_000_000},
    )
    assert state_matches(decision=a, current=b)


def test_changed_relevant_state_is_stale() -> None:
    decision = fingerprint_relevant_state(
        version="liquidity:1",
        state={"capacity": 2_000_000, "reserved": 0, "consumed": 0},
    )
    current = fingerprint_relevant_state(
        version="liquidity:2",
        state={"capacity": 2_000_000, "reserved": 1_500_000, "consumed": 0},
    )
    assert not state_matches(decision=decision, current=current)
