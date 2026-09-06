from __future__ import annotations

from network.load_stress import LoadStressTest


def test_witness_generation_single():
    results = LoadStressTest.make_witness_results(1)

    assert len(results) == 1
    assert results[0]["node_id"] == "node-1"
    assert results[0]["verified"] is True
    assert results[0]["authorized"] is True


def test_witness_generation_large_count():
    results = LoadStressTest.make_witness_results(1000)

    assert len(results) == 1000
    assert results[0]["node_id"] == "node-1"
    assert results[-1]["node_id"] == "node-1000"


def test_witness_generation_same_tip():
    results = LoadStressTest.make_witness_results(
        100,
        chain_tip="tip-test",
    )

    assert all(
        result["chain_tip"] == "tip-test"
        for result in results
    )


def test_witness_generation_deterministic():
    first = LoadStressTest.make_witness_results(
        500,
        chain_tip="tip-deterministic",
    )

    second = LoadStressTest.make_witness_results(
        500,
        chain_tip="tip-deterministic",
    )

    assert first == second


def test_state_hash_deterministic():
    state = {
        "balance": 1000,
        "status": "ACTIVE",
        "owner": "node-1",
    }

    first = LoadStressTest.state_hash(state)
    second = LoadStressTest.state_hash(state)

    assert first == second
    assert len(first) == 64


def test_state_hash_key_order_independent():
    state_a = {
        "balance": 1000,
        "status": "ACTIVE",
        "owner": "node-1",
    }

    state_b = {
        "owner": "node-1",
        "status": "ACTIVE",
        "balance": 1000,
    }

    assert (
        LoadStressTest.state_hash(state_a)
        == LoadStressTest.state_hash(state_b)
    )


def test_state_hash_changes_when_state_changes():
    state_a = {
        "balance": 1000,
        "status": "ACTIVE",
    }

    state_b = {
        "balance": 1001,
        "status": "ACTIVE",
    }

    assert (
        LoadStressTest.state_hash(state_a)
        != LoadStressTest.state_hash(state_b)
    )


def test_hash_benchmark():
    state = {
        "balance": 1000,
        "status": "ACTIVE",
    }

    result = LoadStressTest.benchmark_state_hash(
        state,
        iterations=100,
    )

    assert result["operation"] == "STATE_HASH"
    assert result["iterations"] == 100
    assert result["final_hash"] == LoadStressTest.state_hash(state)
    assert result["deterministic"] is True
    assert result["elapsed_seconds"] >= 0
    assert result["operations_per_second"] > 0


def test_witness_generation_benchmark():
    result = LoadStressTest.benchmark_witness_generation(1000)

    assert result["operation"] == "WITNESS_GENERATION"
    assert result["witness_count"] == 1000
    assert result["generated_count"] == 1000
    assert result["elapsed_seconds"] >= 0
    assert result["witnesses_per_second"] > 0


def test_full_v860_run():
    state = {
        "balance": 1_000_000,
        "escrow": 250_000,
        "status": "ACTIVE",
        "sequence": 86,
    }

    result = LoadStressTest.run(
        witness_count=100,
        hash_iterations=100,
        state=state,
    )

    assert result["version"] == "V86.0"
    assert result["witness_count"] == 100
    assert result["hash_iterations"] == 100
    assert result["deterministic_hash"] is True
    assert result["status"] == "PASS"
    assert len(result["witness_results"]) == 100
    assert (
        result["expected_hash"]
        == LoadStressTest.state_hash(state)
    )