from __future__ import annotations

import hashlib
import json

from network.recovery_integrity_audit import (
    RecoveryIntegrityAudit,
)


def make_state():
    return {
        "balance": 1000,
        "status": "ACTIVE",
    }


def state_hash(state):
    canonical = json.dumps(
        dict(state),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


def make_valid_recovery_result():
    state = make_state()
    source_hash = state_hash(state)

    return {
        "version": "V85.5",
        "status": "RECOVERED",
        "consensus": "QUORUM_REACHED",
        "consensus_count": 3,
        "source_hash": source_hash,
        "state": state,
        "integrity_valid": True,
    }


def test_valid_recovery_passes():
    audit = RecoveryIntegrityAudit()

    result = audit.audit(
        make_valid_recovery_result()
    )

    assert result["status"] == "PASS"
    assert result["accepted"] is True
    assert result["integrity_valid"] is True


def test_audit_does_not_trust_stored_integrity_flag():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    result_data["integrity_valid"] = False

    result = audit.audit(result_data)

    assert result["status"] == "PASS"
    assert result["accepted"] is True


def test_recovery_status_must_be_recovered():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    result_data["status"] = "REJECTED"

    result = audit.audit(result_data)

    assert result["status"] == "REJECTED"
    assert result["accepted"] is False
    assert result["reason"] == "RECOVERY_NOT_VALID"


def test_consensus_must_be_quorum_reached():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    result_data["consensus"] = "NO_QUORUM"

    result = audit.audit(result_data)

    assert result["status"] == "REJECTED"
    assert result["reason"] == "RECOVERY_CONSENSUS_INVALID"


def test_consensus_count_must_be_positive():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    result_data["consensus_count"] = 0

    result = audit.audit(result_data)

    assert result["status"] == "REJECTED"
    assert result["reason"] == "CONSENSUS_COUNT_INVALID"


def test_source_hash_format_is_verified():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    result_data["source_hash"] = "tampered"

    result = audit.audit(result_data)

    assert result["status"] == "REJECTED"
    assert result["reason"] == "SOURCE_HASH_INVALID"


def test_recovered_state_hash_is_recomputed():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    result_data["state"] = {
        "balance": 9999,
        "status": "ACTIVE",
    }

    result = audit.audit(result_data)

    assert result["status"] == "REJECTED"
    assert result["reason"] == "RECOVERED_STATE_HASH_MISMATCH"
    assert result["integrity_valid"] is False


def test_missing_recovered_state_is_rejected():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    del result_data["state"]

    result = audit.audit(result_data)

    assert result["status"] == "REJECTED"
    assert result["reason"] == "RECOVERED_STATE_INVALID"


def test_source_hash_and_state_hash_must_match():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    original_hash = result_data["source_hash"]

    result = audit.audit(result_data)

    assert result["source_hash"] == original_hash
    assert (
        result["source_hash"]
        == result["recovered_state_hash"]
    )
    assert result["status"] == "PASS"


def test_tampered_integrity_flag_cannot_force_pass_or_reject():
    audit = RecoveryIntegrityAudit()

    result_data = make_valid_recovery_result()

    result_data["integrity_valid"] = False

    result = audit.audit(result_data)

    assert result["status"] == "PASS"
    assert result["accepted"] is True
    assert result["recovered_state_hash_valid"] is True