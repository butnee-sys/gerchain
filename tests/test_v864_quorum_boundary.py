from __future__ import annotations

import pytest

from network.load_stress_quorum_boundary import (
    QuorumBoundaryLoadStressTest,
)


def test_all_witnesses_failed_is_rejected():
    state = QuorumBoundaryLoadStressTest.make_state()

    result = QuorumBoundaryLoadStressTest.run(
        witness_count=5,
        failure_count=5,
        state=state,
        chain_tip="tip-all-failed",
    )

    assert result["active_count"] == 0
    assert result["quorum_reached"] is False
    assert result["recovery_rejected"] is True
    assert result["audit_not_pass"] is True
    assert result["safe_rejection"] is True
    assert result["status"] == "PASS"


def test_no_quorum_does_not_recover_state():
    state = QuorumBoundaryLoadStressTest.make_state(
        sequence=864,
        balance=2_000_000,
    )

    result = QuorumBoundaryLoadStressTest.run(
        witness_count=10,
        failure_count=10,
        state=state,
        chain_tip="tip-no-quorum",
    )

    assert result["recovery"]["status"] == "REJECTED"
    assert result["recovery"]["reason"] == (
        "RECOVERY_QUORUM_NOT_REACHED"
    )
    assert result["audit"]["status"] == "REJECTED"


def test_no_quorum_cannot_produce_integrity_pass():
    state = QuorumBoundaryLoadStressTest.make_state()

    result = QuorumBoundaryLoadStressTest.run(
        witness_count=20,
        failure_count=20,
        state=state,
    )

    assert result["quorum_reached"] is False
    assert result["audit"]["status"] != "PASS"
    assert result["audit"]["accepted"] is False


def test_safe_rejection_flag():
    state = QuorumBoundaryLoadStressTest.make_state()

    result = QuorumBoundaryLoadStressTest.run(
        witness_count=10,
        failure_count=10,
        state=state,
    )

    assert result["safe_rejection"] is True
    assert result["status"] == "PASS"


def test_large_no_quorum_network():
    state = QuorumBoundaryLoadStressTest.make_state(
        sequence=86_400,
        balance=100_000_000,
    )

    result = QuorumBoundaryLoadStressTest.run(
        witness_count=1000,
        failure_count=1000,
        state=state,
        chain_tip="tip-large-rejection",
    )

    assert result["active_count"] == 0
    assert result["quorum_reached"] is False
    assert result["recovery"]["status"] == "REJECTED"
    assert result["audit"]["status"] == "REJECTED"
    assert result["safe_rejection"] is True
    assert result["status"] == "PASS"


def test_failed_nodes_are_all_recorded():
    result = QuorumBoundaryLoadStressTest.run(
        witness_count=100,
        failure_count=100,
        state=QuorumBoundaryLoadStressTest.make_state(),
    )

    assert len(result["failed_nodes"]) == 100
    assert result["failed_nodes"][0] == "node-1"
    assert result["failed_nodes"][-1] == "node-100"


def test_failure_count_cannot_exceed_witness_count():
    with pytest.raises(ValueError):
        QuorumBoundaryLoadStressTest.make_failed_nodes(
            witness_count=10,
            failure_count=11,
        )


def test_negative_failure_count_rejected():
    with pytest.raises(ValueError):
        QuorumBoundaryLoadStressTest.make_failed_nodes(
            witness_count=10,
            failure_count=-1,
        )


def test_quorum_boundary_benchmark_safe_rejection():
    state = QuorumBoundaryLoadStressTest.make_state()

    result = QuorumBoundaryLoadStressTest.benchmark(
        witness_count=100,
        failure_count=100,
        iterations=100,
        state=state,
        chain_tip="tip-boundary",
    )

    assert result["version"] == "V86.4"
    assert result["operation"] == (
        "QUORUM_BOUNDARY_BENCHMARK"
    )
    assert result["witness_count"] == 100
    assert result["failure_count"] == 100
    assert result["iterations"] == 100
    assert result["active_count"] == 0
    assert result["safe_rejection"] is True
    assert result["status"] == "PASS"
    assert result["final_recovery"]["status"] == "REJECTED"
    assert result["final_audit"]["status"] == "REJECTED"


def test_quorum_boundary_is_deterministic():
    state = QuorumBoundaryLoadStressTest.make_state(
        sequence=864,
        balance=9_000_000,
    )

    first = QuorumBoundaryLoadStressTest.run(
        witness_count=50,
        failure_count=50,
        state=state,
        chain_tip="tip-deterministic",
    )

    second = QuorumBoundaryLoadStressTest.run(
        witness_count=50,
        failure_count=50,
        state=state,
        chain_tip="tip-deterministic",
    )

    assert first["status"] == "PASS"
    assert second["status"] == "PASS"

    assert (
        first["recovery"]["status"]
        == second["recovery"]["status"]
    )

    assert (
        first["recovery"]["reason"]
        == second["recovery"]["reason"]
    )

    assert (
        first["audit"]["status"]
        == second["audit"]["status"]
    )

    assert first["safe_rejection"] is True
    assert second["safe_rejection"] is True