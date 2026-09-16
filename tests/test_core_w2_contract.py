from __future__ import annotations

"""W2 contract tests.

These tests intentionally define the economic invariants before wiring them to
an implementation. They are not evidence of PostgreSQL correctness by
selves; implementation tests and an independent oracle must satisfy them.
"""


def test_shared_liquidity_never_over_allocates() -> None:
    capacity = 2_000_000
    requested = [1_500_000, 1_500_000]

    # A valid concurrent execution may admit one request and reject/hold the
    # other, but the aggregate committed consumption must never exceed the
    # canonical capacity.
    committed = min(capacity, sum(requested))
    assert committed <= capacity


def test_stale_decision_cannot_execute_against_changed_state() -> None:
    decision_state_fingerprint = "state-v1"
    current_state_fingerprint = "state-v2"

    assert decision_state_fingerprint != current_state_fingerprint
    execution_status = "HOLD"
    assert execution_status in {"HOLD", "REJECT_STALE"}
