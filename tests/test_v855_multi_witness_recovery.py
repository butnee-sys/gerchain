from __future__ import annotations

import hashlib

from network.multi_witness_recovery import MultiWitnessRecovery


def make_result(node_id, chain_tip="tip-a", verified=True, authorized=True):
    return {
        "node_id": node_id,
        "verified": verified,
        "authorized": authorized,
        "chain_tip": chain_tip,
    }


def make_state():
    return {
        "balance": 1000,
        "status": "ACTIVE",
    }


def state_hash(state):
    import json

    canonical = json.dumps(
        dict(state),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def test_valid_multi_witness_recovery():
    recovery = MultiWitnessRecovery()

    state = make_state()
    expected_hash = state_hash(state)

    results = [
        make_result("node-1"),
        make_result("node-2"),
        make_result("node-3"),
    ]

    result = recovery.recover(
        results,
        state,
        expected_hash,
    )

    assert result["status"] == "RECOVERED"
    assert result["consensus"] == "QUORUM_REACHED"
    assert result["state"] == state
    assert result["integrity_valid"] is True


def test_failed_witness_is_excluded():
    recovery = MultiWitnessRecovery()

    results = [
        make_result("node-1"),
        make_result("node-2"),
        make_result("node-3"),
    ]

    consensus = recovery.determine_recovery_consensus(
        results,
        failed_nodes=["node-2"],
    )

    assert "node-2" not in consensus["active_nodes"]
    assert "node-2" not in consensus["consensus_nodes"]
    assert consensus["consensus"] == "QUORUM_REACHED"


def test_all_witnesses_available():
    recovery = MultiWitnessRecovery()

    results = [
        make_result("node-1"),
        make_result("node-2"),
        make_result("node-3"),
    ]

    result = recovery.determine_recovery_consensus(results)

    assert result["active_count"] == 3
    assert result["failed_nodes"] == []
    assert result["consensus"] == "QUORUM_REACHED"


def test_recovery_rejected_without_quorum():
    recovery = MultiWitnessRecovery()

    state = make_state()
    expected_hash = state_hash(state)

    results = [
        make_result("node-1"),
    ]

    result = recovery.recover(
        results,
        state,
        expected_hash,
    )

    assert result["status"] == "REJECTED"
    assert result["reason"] == "RECOVERY_QUORUM_NOT_REACHED"


def test_recovery_rejected_when_source_state_tampered():
    recovery = MultiWitnessRecovery()

    original_state = make_state()
    expected_hash = state_hash(original_state)

    tampered_state = {
        "balance": 9999,
        "status": "ACTIVE",
    }

    results = [
        make_result("node-1"),
        make_result("node-2"),
        make_result("node-3"),
    ]

    result = recovery.recover(
        results,
        tampered_state,
        expected_hash,
    )

    assert result["status"] == "REJECTED"
    assert result["reason"] == "SOURCE_STATE_HASH_MISMATCH"


def test_conflicting_chain_tips_do_not_create_fake_consensus():
    recovery = MultiWitnessRecovery()

    results = [
        make_result("node-1", chain_tip="tip-a"),
        make_result("node-2", chain_tip="tip-b"),
        make_result("node-3", chain_tip="tip-c"),
    ]

    result = recovery.determine_recovery_consensus(results)

    assert result["consensus"] != "QUORUM_REACHED"


def test_failed_majority_prevents_recovery():
    recovery = MultiWitnessRecovery()

    state = make_state()
    expected_hash = state_hash(state)

    results = [
        make_result("node-1"),
        make_result("node-2"),
        make_result("node-3"),
    ]

    result = recovery.recover(
        results,
        state,
        expected_hash,
        failed_nodes=[
            "node-1",
            "node-2",
        ],
    )

    assert result["status"] == "REJECTED"
    assert result["reason"] == "RECOVERY_QUORUM_NOT_REACHED"


def test_unauthorized_witness_does_not_count():
    recovery = MultiWitnessRecovery()

    results = [
        make_result("node-1", authorized=True),
        make_result("node-2", authorized=False),
        make_result("node-3", authorized=True),
    ]

    result = recovery.determine_recovery_consensus(results)

    assert "node-2" not in result["consensus_nodes"]


def test_invalid_witness_does_not_count():
    recovery = MultiWitnessRecovery()

    results = [
        make_result("node-1", verified=True),
        make_result("node-2", verified=False),
        make_result("node-3", verified=True),
    ]

    result = recovery.determine_recovery_consensus(results)

    assert "node-2" not in result["consensus_nodes"]


def test_failed_and_invalid_witnesses_are_both_excluded():
    recovery = MultiWitnessRecovery()

    results = [
        make_result("node-1"),
        make_result("node-2", verified=False),
        make_result("node-3"),
        make_result("node-4"),
    ]

    result = recovery.determine_recovery_consensus(
        results,
        failed_nodes=["node-4"],
    )

    assert "node-2" not in result["consensus_nodes"]
    assert "node-4" not in result["consensus_nodes"]
    assert "node-1" in result["consensus_nodes"]
    assert "node-3" in result["consensus_nodes"]