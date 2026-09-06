from __future__ import annotations

import pytest

from network.load_stress_quorum_threshold import (
    QuorumThresholdLoadStressTest,
)


def test_no_active_witnesses_rejected():
    state = QuorumThresholdLoadStressTest.make_state()

    result = QuorumThresholdLoadStressTest.run(
        witness_count=10,
        failure_count=10,
        state=state,
    )

    assert result["active_count"] == 0
    assert result["quorum_reached"] is False
    assert result["recovery_accepted"] is False
    assert result["audit_pass"] is False
    assert result["status"] == "PASS"


def test_full_active_witnesses_reach_consensus():
    state = QuorumThresholdLoadStressTest.make_state()

    result = QuorumThresholdLoadStressTest.run(
        witness_count=10,
        failure_count=0,
        state=state,
    )

    assert result["active_count"] == 10
    assert result["quorum_reached"] is True
    assert result["recovery_accepted"] is True
    assert result["audit_pass"] is True
    assert result["status"] == "PASS"


def test_threshold_behavior_is_consistent():
    state = QuorumThresholdLoadStressTest.make_state()

    results = []

    for failure_count in range(11):
        result = QuorumThresholdLoadStressTest.run(
            witness_count=10,
            failure_count=failure_count,
            state=state,
        )
        results.append(result)

        assert result["status"] == "PASS"

        assert (
            result["quorum_reached"]
            == result["recovery_accepted"]
            == result["audit_pass"]
        )

    assert results[0]["quorum_reached"] is True
    assert results[-1]["quorum_reached"] is False


def test_quorum_does_not_appear_after_more_failures():
    state = QuorumThresholdLoadStressTest.make_state()

    previous_quorum = True

    for failure_count in range(11):
        result = QuorumThresholdLoadStressTest.run(
            witness_count=10,
            failure_count=failure_count,
            state=state,
        )

        current_quorum = result["quorum_reached"]

        if previous_quorum is False:
            assert current_quorum is False

        previous_quorum = current_quorum


def test_active_count_matches_failure_count():
    state = QuorumThresholdLoadStressTest.make_state()

    for failure_count in range(11):
        result = QuorumThresholdLoadStressTest.run(
            witness_count=10,
            failure_count=failure_count,
            state=state,
        )

        assert result["active_count"] == (
            10 - failure_count
        )


def test_failed_nodes_match_active_boundary():
    state = QuorumThresholdLoadStressTest.make_state()

    result = QuorumThresholdLoadStressTest.run(
        witness_count=20,
        failure_count=7,
        state=state,
        chain_tip="tip-boundary",
    )

    assert len(result["failed_nodes"]) == 7
    assert result["active_count"] == 13
    assert result["chain_tip"] == "tip-boundary"
    assert result["status"] == "PASS"


def test_large_network_threshold_consistency():
    state = QuorumThresholdLoadStressTest.make_state(
        sequence=8650,
        balance=50_000_000,
    )

    results = []

    for failure_count in (
        0,
        100,
        250,
        500,
        750,
        1000,
    ):
        result = QuorumThresholdLoadStressTest.run(
            witness_count=1000,
            failure_count=failure_count,
            state=state,
        )

        assert result["status"] == "PASS"

        assert (
            result["quorum_reached"]
            == result["recovery_accepted"]
            == result["audit_pass"]
        )

        results.append(result)

    assert results[0]["quorum_reached"] is True
    assert results[-1]["quorum_reached"] is False


def test_benchmark_preserves_threshold_decision():
    state = QuorumThresholdLoadStressTest.make_state()

    result = QuorumThresholdLoadStressTest.benchmark(
        witness_count=100,
        failure_count=100,
        iterations=100,
        state=state,
        chain_tip="tip-benchmark",
    )

    assert result["version"] == "V86.5"
    assert result["iterations"] == 100
    assert result["active_count"] == 0
    assert result["quorum_reached"] is False
    assert result["recovery_accepted"] is False
    assert result["audit_pass"] is False
    assert result["consistent"] is True
    assert result["status"] == "PASS"


def test_threshold_decision_is_deterministic():
    state = QuorumThresholdLoadStressTest.make_state(
        sequence=865,
        balance=9_000_000,
    )

    first = QuorumThresholdLoadStressTest.run(
        witness_count=50,
        failure_count=25,
        state=state,
        chain_tip="tip-deterministic",
    )

    second = QuorumThresholdLoadStressTest.run(
        witness_count=50,
        failure_count=25,
        state=state,
        chain_tip="tip-deterministic",
    )

    assert first["status"] == "PASS"
    assert second["status"] == "PASS"

    assert (
        first["quorum_reached"]
        == second["quorum_reached"]
    )

    assert (
        first["recovery_accepted"]
        == second["recovery_accepted"]
    )

    assert (
        first["audit_pass"]
        == second["audit_pass"]
    )


def test_invalid_threshold_inputs_rejected():
    state = QuorumThresholdLoadStressTest.make_state()

    with pytest.raises(ValueError):
        QuorumThresholdLoadStressTest.run(
            witness_count=10,
            failure_count=11,
            state=state,
        )

    with pytest.raises(ValueError):
        QuorumThresholdLoadStressTest.run(
            witness_count=10,
            failure_count=-1,
            state=state,
        )

    with pytest.raises(ValueError):
        QuorumThresholdLoadStressTest.run(
            witness_count=0,
            failure_count=0,
            state=state,
        )