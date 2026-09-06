from __future__ import annotations

import pytest

from network.load_stress_consensus import ConsensusLoadStressTest


def test_make_consensus_results_single_witness():
    results = ConsensusLoadStressTest.make_consensus_results(1)

    assert len(results) == 1
    assert results[0]["node_id"] == "node-1"
    assert results[0]["verified"] is True
    assert results[0]["authorized"] is True
    assert results[0]["chain_tip"] == "tip-a"


def test_make_consensus_results_large_witness_count():
    results = ConsensusLoadStressTest.make_consensus_results(1000)

    assert len(results) == 1000
    assert results[0]["node_id"] == "node-1"
    assert results[-1]["node_id"] == "node-1000"


def test_make_consensus_results_custom_tip():
    results = ConsensusLoadStressTest.make_consensus_results(
        100,
        chain_tip="tip-custom",
    )

    assert len(results) == 100
    assert all(
        result["chain_tip"] == "tip-custom"
        for result in results
    )


def test_make_consensus_results_deterministic():
    first = ConsensusLoadStressTest.make_consensus_results(
        500,
        chain_tip="tip-deterministic",
    )

    second = ConsensusLoadStressTest.make_consensus_results(
        500,
        chain_tip="tip-deterministic",
    )

    assert first == second


def test_run_consensus_reaches_quorum():
    result = ConsensusLoadStressTest.run_consensus(
        witness_count=5,
        chain_tip="tip-a",
    )

    assert result["version"] == "V86.1"
    assert result["operation"] == "CONSENSUS"
    assert result["witness_count"] == 5
    assert result["consensus"] == "QUORUM_REACHED"
    assert result["chain_tip"] == "tip-a"
    assert result["consensus_count"] == 5
    assert len(result["consensus_nodes"]) == 5


def test_run_consensus_large_network():
    result = ConsensusLoadStressTest.run_consensus(
        witness_count=1000,
        chain_tip="tip-large",
    )

    assert result["consensus"] == "QUORUM_REACHED"
    assert result["chain_tip"] == "tip-large"
    assert result["consensus_count"] == 1000
    assert len(result["consensus_nodes"]) == 1000
    assert result["elapsed_seconds"] >= 0


def test_consensus_benchmark():
    result = ConsensusLoadStressTest.benchmark(
        witness_count=100,
        iterations=100,
        chain_tip="tip-benchmark",
    )

    assert result["version"] == "V86.1"
    assert result["operation"] == "CONSENSUS_BENCHMARK"
    assert result["witness_count"] == 100
    assert result["iterations"] == 100
    assert result["elapsed_seconds"] >= 0
    assert result["operations_per_second"] > 0
    assert result["deterministic"] is True

    final_consensus = result["final_consensus"]

    assert final_consensus["consensus"] == "QUORUM_REACHED"
    assert final_consensus["chain_tip"] == "tip-benchmark"
    assert final_consensus["count"] == 100


def test_consensus_determinism_check():
    result = ConsensusLoadStressTest.run_determinism_check(
        witness_count=100,
        chain_tip="tip-deterministic",
    )

    assert result["version"] == "V86.1"
    assert result["operation"] == "DETERMINISM_CHECK"
    assert result["witness_count"] == 100
    assert result["deterministic"] is True
    assert result["status"] == "PASS"


def test_consensus_different_tip_changes_result():
    first = ConsensusLoadStressTest.run_consensus(
        witness_count=50,
        chain_tip="tip-a",
    )

    second = ConsensusLoadStressTest.run_consensus(
        witness_count=50,
        chain_tip="tip-b",
    )

    assert first["consensus"] == "QUORUM_REACHED"
    assert second["consensus"] == "QUORUM_REACHED"

    assert first["chain_tip"] == "tip-a"
    assert second["chain_tip"] == "tip-b"

    assert first["chain_tip"] != second["chain_tip"]


def test_invalid_witness_count_rejected():
    with pytest.raises(ValueError):
        ConsensusLoadStressTest.make_consensus_results(0)

    with pytest.raises(ValueError):
        ConsensusLoadStressTest.make_consensus_results(-1)