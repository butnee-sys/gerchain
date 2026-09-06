from __future__ import annotations

import pytest

from network.load_stress_failure import (
    FailureInjectionLoadStressTest,
)


def test_make_node_results_single():
    results = FailureInjectionLoadStressTest.make_node_results(1)

    assert len(results) == 1
    assert results[0]["node_id"] == "node-1"
    assert results[0]["verified"] is True
    assert results[0]["authorized"] is True


def test_make_node_results_large():
    results = FailureInjectionLoadStressTest.make_node_results(
        1000,
        chain_tip="tip-large",
    )

    assert len(results) == 1000
    assert results[0]["node_id"] == "node-1"
    assert results[-1]["node_id"] == "node-1000"
    assert all(
        item["chain_tip"] == "tip-large"
        for item in results
    )


def test_make_failed_nodes():
    failed = FailureInjectionLoadStressTest.make_failed_nodes(
        witness_count=10,
        failure_count=3,
    )

    assert failed == [
        "node-1",
        "node-2",
        "node-3",
    ]


def test_no_failures():
    failed = FailureInjectionLoadStressTest.make_failed_nodes(
        witness_count=10,
        failure_count=0,
    )

    assert failed == []


def test_failure_isolation():
    state = FailureInjectionLoadStressTest.make_state()

    result = FailureInjectionLoadStressTest.run(
        witness_count=10,
        failure_count=2,
        state=state,
        chain_tip="tip-a",
    )

    assert result["status"] == "PASS"
    assert result["failed_nodes"] == [
        "node-1",
        "node-2",
    ]
    assert result["failed_nodes_isolated"] is True

    for item in result["failure_statuses"]:
        assert item["isolation_status"] == "ISOLATED"
        assert item["participates_in_consensus"] is False


def test_recovery_with_single_failure():
    state = FailureInjectionLoadStressTest.make_state()

    result = FailureInjectionLoadStressTest.run(
        witness_count=10,
        failure_count=1,
        state=state,
        chain_tip="tip-recovery",
    )

    assert result["status"] == "PASS"
    assert result["recovery"]["status"] == "RECOVERED"
    assert result["audit"]["status"] == "PASS"
    assert result["audit"]["accepted"] is True

    assert "node-1" not in (
        result["recovery"]["active_nodes"]
    )


def test_recovery_with_multiple_failures():
    state = FailureInjectionLoadStressTest.make_state(
        sequence=863,
        balance=5_000_000,
    )

    result = FailureInjectionLoadStressTest.run(
        witness_count=100,
        failure_count=20,
        state=state,
        chain_tip="tip-multi-failure",
    )

    assert result["status"] == "PASS"
    assert result["recovery"]["status"] == "RECOVERED"
    assert result["audit"]["status"] == "PASS"

    assert result["recovery"]["consensus_count"] == 80
    assert len(result["recovery"]["active_nodes"]) == 80


def test_large_failure_injection():
    state = FailureInjectionLoadStressTest.make_state(
        sequence=86_300,
        balance=100_000_000,
    )

    result = FailureInjectionLoadStressTest.run(
        witness_count=1000,
        failure_count=100,
        state=state,
        chain_tip="tip-large-failure",
    )

    assert result["status"] == "PASS"
    assert result["failed_nodes_isolated"] is True
    assert result["recovery"]["status"] == "RECOVERED"
    assert result["audit"]["status"] == "PASS"
    assert result["recovery"]["consensus_count"] == 900


def test_failure_benchmark():
    state = FailureInjectionLoadStressTest.make_state()

    result = FailureInjectionLoadStressTest.benchmark(
        witness_count=100,
        failure_count=10,
        iterations=100,
        state=state,
        chain_tip="tip-benchmark",
    )

    assert result["version"] == "V86.3"
    assert result["operation"] == (
        "FAILURE_INJECTION_BENCHMARK"
    )
    assert result["witness_count"] == 100
    assert result["failure_count"] == 10
    assert result["iterations"] == 100
    assert result["elapsed_seconds"] >= 0
    assert result["operations_per_second"] > 0
    assert result["deterministic"] is True
    assert result["status"] == "PASS"

    assert result["final_recovery"]["status"] == "RECOVERED"
    assert result["final_audit"]["status"] == "PASS"


def test_invalid_failure_counts_rejected():
    with pytest.raises(ValueError):
        FailureInjectionLoadStressTest.make_failed_nodes(
            witness_count=10,
            failure_count=-1,
        )

    with pytest.raises(ValueError):
        FailureInjectionLoadStressTest.make_failed_nodes(
            witness_count=10,
            failure_count=11,
        )

    with pytest.raises(ValueError):
        FailureInjectionLoadStressTest.make_failed_nodes(
            witness_count=0,
            failure_count=0,
        )