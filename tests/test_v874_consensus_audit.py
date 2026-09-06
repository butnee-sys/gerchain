import pytest
from network.security_consensus_audit import ConsensusAuditEngine

def test_consensus_pass():
    engine = ConsensusAuditEngine(required_quorum=2)
    witnesses = ["node_a", "node_b", "node_c"]
    signatures = {"node_a": True, "node_b": True, "node_c": False}
    assert engine.audit_consensus(witnesses, signatures) == "PASS"

def test_consensus_rejected_below_quorum():
    engine = ConsensusAuditEngine(required_quorum=2)
    witnesses = ["node_a", "node_b", "node_c"]
    signatures = {"node_a": True, "node_b": False, "node_c": False}
    assert engine.audit_consensus(witnesses, signatures) == "REJECTED"

def test_consensus_inconclusive_missing_params():
    engine = ConsensusAuditEngine(required_quorum=2)
    assert engine.audit_consensus([], {"node_a": True}) == "INCONCLUSIVE"
    assert engine.audit_consensus(["node_a"], {}) == "INCONCLUSIVE"