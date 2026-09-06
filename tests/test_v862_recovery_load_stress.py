from __future__ import annotations

import pytest

from network.load_stress_recovery import RecoveryLoadStressTest


def test_make_node_results_single_witness():
    results = RecoveryLoadStressTest.make_node_results(1)

    assert len(results) == 1
    assert results[0]["node_id"] == "node-1"
    assert results[0]["verified"] is True
    assert results[0]["authorized"] is True
    assert results[0]["chain_tip"] == "tip-a"


def test_make_node_results_large_network():
    results = RecoveryLoadStressTest.make_node_results(
        1000,
        chain_tip="tip-large",
    )

    assert len(results) == 1000
    assert results[0]["node_id"] == "node-1"
    assert results[-1]["node_id"] == "node-1000"
    assert all(
        result["chain_tip"] == "tip-large"
        for result in results
    )


def test_make_state_deterministic():
    first = RecoveryLoadStressTest.make_state(
        sequence=862,
        balance=1_000_000,
    )

    second = RecoveryLoadStressTest.make_state(
        sequence=862,
        balance=1_000_000,
    )

    assert first == second


def test_run_recovery_integrity_passes():
    state = RecoveryLoadStressTest.make_state()

    result = RecoveryLoadStressTest.run(
        witness_count=5,
        state=state,
        chain_tip="tip-a",
    )

    assert result["version"] == "V86.2"
    assert result["operation"] == "RECOVERY_INTEGRITY"
    assert result["witness_count"] == 5
    assert result["chain_tip"] == "tip-a"
    assert result["status"] == "PASS"

    assert result["recovery"]["status"] == "RECOVERED"
    assert result["audit"]["status"] == "PASS"
    assert result["audit"]["accepted"] is True


def test_large_recovery_integrity():
    state = RecoveryLoadStressTest.make_state(
        sequence=10_000,
        balance=50_000_000,
    )

    result = RecoveryLoadStressTest.run(
        witness_count=1000,
        state=state,
        chain_tip="tip-large",
    )

    assert result["status"] == "PASS"
    assert result["recovery"]["status"] == "RECOVERED"
    assert result["audit"]["status"] == "PASS"
    assert result["recovery"]["consensus"] == "QUORUM_REACHED"
    assert result["recovery"]["consensus_count"] == 1000


def test_failed_witness_is_excluded():
    state = RecoveryLoadStressTest.make_state()

    result = RecoveryLoadStressTest.run(
        witness_count=5,
        state=state,
        chain_tip="tip-a",
        failed_nodes=["node-1"],
    )

    assert result["status"] == "PASS"
    assert result["recovery"]["status"] == "RECOVERED"
    assert "node-1" not in result["recovery"]["active_nodes"]
    assert result["recovery"]["failed_nodes"] == ["node-1"]


def test_recovered_state_matches_source():
    state = RecoveryLoadStressTest.make_state(
        sequence=999,
        balance=7_500_000,
    )

    result = RecoveryLoadStressTest.run(
        witness_count=10,
        state=state,
        chain_tip="tip-state",
    )

    recovered_state = result["recovery"]["state"]

    assert recovered_state == state
    assert result["audit"]["source_hash"] == (
        result["audit"]["recovered_state_hash"]
    )


def test_benchmark_passes():
    state = RecoveryLoadStressTest.make_state()

    result = RecoveryLoadStressTest.benchmark(
        witness_count=100,
        iterations=100,
        state=state,
        chain_tip="tip-benchmark",
    )

    assert result["version"] == "V86.2"
    assert result["operation"] == (
        "RECOVERY_INTEGRITY_BENCHMARK"
    )
    assert result["witness_count"] == 100
    assert result["iterations"] == 100
    assert result["elapsed_seconds"] >= 0
    assert result["operations_per_second"] > 0
    assert result["deterministic"] is True
    assert result["status"] == "PASS"

    assert result["final_recovery"]["status"] == "RECOVERED"
    assert result["final_audit"]["status"] == "PASS"


def test_different_chain_tip_is_preserved():
    state = RecoveryLoadStressTest.make_state()

    first = RecoveryLoadStressTest.run(
        witness_count=20,
        state=state,
        chain_tip="tip-a",
    )

    second = RecoveryLoadStressTest.run(
        witness_count=20,
        state=state,
        chain_tip="tip-b",
    )

    assert first["status"] == "PASS"
    assert second["status"] == "PASS"

    assert first["chain_tip"] == "tip-a"
    assert second["chain_tip"] == "tip-b"

    assert (
        first["recovery"]["chain_tip"]
        != second["recovery"]["chain_tip"]
    )


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        RecoveryLoadStressTest.make_node_results(0)

    with pytest.raises(ValueError):
        RecoveryLoadStressTest.make_node_results(-1)

    with pytest.raises(TypeError):
        RecoveryLoadStressTest.make_state(
            sequence="invalid"
        )

    with pytest.raises(ValueError):
        RecoveryLoadStressTest.benchmark(
            witness_count=10,
            iterations=0,
            state=RecoveryLoadStressTest.make_state(),
        )