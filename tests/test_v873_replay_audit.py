import pytest
from network.security_replay_audit import ReplayAuditEngine

def test_replay_audit_fresh_event():
    engine = ReplayAuditEngine()
    result = engine.audit_event("evt_001", "hash_abc123", "nonce_999")
    assert result == "PASS"

def test_replay_audit_duplicate_hash():
    engine = ReplayAuditEngine()
    # First time: Fresh
    assert engine.audit_event("evt_001", "hash_abc123", "nonce_999") == "PASS"
    # Second time with same hash: Replay Attack
    assert engine.audit_event("evt_002", "hash_abc123", "nonce_888") == "REJECTED"

def test_replay_audit_duplicate_nonce():
    engine = ReplayAuditEngine()
    # First time: Fresh
    assert engine.audit_event("evt_001", "hash_abc123", "nonce_999") == "PASS"
    # Second time with same nonce: Replay Attack
    assert engine.audit_event("evt_002", "hash_xyz789", "nonce_999") == "REJECTED"

def test_replay_audit_inconclusive():
    engine = ReplayAuditEngine()
    # Missing parameters
    assert engine.audit_event("", "hash_abc123", "nonce_999") == "INCONCLUSIVE"
    assert engine.audit_event("evt_001", "", "nonce_999") == "INCONCLUSIVE"
    assert engine.audit_event("evt_001", "hash_abc123", "") == "INCONCLUSIVE"