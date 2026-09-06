from network.failure import FailureStatus
from network.failure_isolation import WitnessFailureIsolation
from network.state_recovery import StateRecovery


def test_state_hash_is_deterministic():
    recovery = StateRecovery()
    state = {"balance": 100, "status": "LOCKED"}

    assert recovery.state_hash(state) == recovery.state_hash(state)


def test_source_state_hash_verification_passes():
    recovery = StateRecovery()
    state = {"balance": 100, "status": "LOCKED"}
    expected_hash = recovery.state_hash(state)

    assert recovery.verify_source_state(state, expected_hash) is True


def test_source_state_hash_mismatch_rejected():
    recovery = StateRecovery()
    state = {"balance": 100, "status": "LOCKED"}

    assert recovery.verify_source_state(state, "invalid_hash") is False


def test_non_isolated_node_cannot_recover():
    recovery = StateRecovery()
    status = FailureStatus("node-A", True)
    state = {"balance": 100}

    result = recovery.recover(
        status,
        state,
        recovery.state_hash(state),
    )

    assert result["status"] == "REJECTED"
    assert result["reason"] == "NODE_IS_NOT_ISOLATED"


def test_isolated_node_can_recover_valid_state():
    recovery = StateRecovery()
    status = FailureStatus("node-A", False, "timeout")
    state = {"balance": 100, "status": "LOCKED"}
    state_hash = recovery.state_hash(state)

    result = recovery.recover(status, state, state_hash)

    assert result["status"] == "RECOVERED"
    assert result["node_id"] == "node-A"
    assert result["integrity_valid"] is True


def test_recovered_hash_matches_source_hash():
    recovery = StateRecovery()
    status = FailureStatus("node-A", False, "offline")
    state = {"balance": 250, "status": "LOCKED"}
    state_hash = recovery.state_hash(state)

    result = recovery.recover(status, state, state_hash)

    assert result["source_hash"] == state_hash
    assert result["recovered_hash"] == state_hash


def test_tampered_source_state_is_rejected():
    recovery = StateRecovery()
    status = FailureStatus("node-A", False, "timeout")
    original_state = {"balance": 100, "status": "LOCKED"}
    expected_hash = recovery.state_hash(original_state)

    tampered_state = {"balance": 999, "status": "LOCKED"}

    result = recovery.recover(
        status,
        tampered_state,
        expected_hash,
    )

    assert result["status"] == "REJECTED"
    assert result["reason"] == "SOURCE_STATE_HASH_MISMATCH"


def test_recovered_state_equals_source_state():
    recovery = StateRecovery()
    status = FailureStatus("node-A", False, "connection_lost")
    state = {
        "balance": 500,
        "status": "LOCKED",
        "sequence": 12,
    }
    state_hash = recovery.state_hash(state)

    result = recovery.recover(status, state, state_hash)

    assert result["state"] == state


def test_recovery_is_deterministic():
    recovery = StateRecovery()
    status = FailureStatus("node-A", False, "timeout")
    state = {"balance": 300, "status": "LOCKED"}
    state_hash = recovery.state_hash(state)

    first = recovery.recover(status, state, state_hash)
    second = recovery.recover(status, state, state_hash)

    assert first == second


def test_recovery_version_is_v852():
    recovery = StateRecovery()
    status = FailureStatus("node-A", False, "timeout")
    state = {"balance": 100}
    state_hash = recovery.state_hash(state)

    result = recovery.recover(status, state, state_hash)

    assert result["version"] == "V85.2"