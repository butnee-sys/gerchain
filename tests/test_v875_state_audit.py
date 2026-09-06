import pytest
from network.security_state_audit import StateAuditEngine

def test_state_01_pending_to_locked():
    engine = StateAuditEngine()
    assert engine.audit_transition("PENDING", "LOCKED") == "PASS"

def test_state_02_pending_to_cancelled():
    engine = StateAuditEngine()
    assert engine.audit_transition("PENDING", "CANCELLED") == "PASS"

def test_state_03_locked_to_released():
    engine = StateAuditEngine()
    assert engine.audit_transition("LOCKED", "RELEASED") == "PASS"

def test_state_04_locked_to_refunded():
    engine = StateAuditEngine()
    assert engine.audit_transition("LOCKED", "REFUNDED") == "PASS"

def test_state_05_pending_to_released_invalid():
    engine = StateAuditEngine()
    assert engine.audit_transition("PENDING", "RELEASED") == "REJECTED"

def test_state_06_released_to_pending_invalid():
    engine = StateAuditEngine()
    assert engine.audit_transition("RELEASED", "PENDING") == "REJECTED"

def test_state_07_cancelled_to_locked_invalid():
    engine = StateAuditEngine()
    assert engine.audit_transition("CANCELLED", "LOCKED") == "REJECTED"

def test_state_08_empty_current_state():
    engine = StateAuditEngine()
    assert engine.audit_transition("", "LOCKED") == "INCONCLUSIVE"

def test_state_09_empty_next_state():
    engine = StateAuditEngine()
    assert engine.audit_transition("PENDING", "") == "INCONCLUSIVE"

def test_state_10_unknown_state():
    engine = StateAuditEngine()
    assert engine.audit_transition("PENDING", "UNKNOWN_STATE") == "INCONCLUSIVE"