from dee_security.audit import append_record, verify_chain


def test_unified_audit_chain_covers_governance_execution_context():
    first = append_record(sequence=1, event="AUTHORIZE", change_id="REQ-1", owner_id="OWNER-001", decision="ALLOW", stage="GATEWAY", connector_id="EXIM-A", request_id="REQ-1", operation="release")
    second = append_record(sequence=2, event="EXECUTE", change_id="REQ-1", owner_id="OWNER-001", decision="ALLOW", previous_hash=first.record_hash, stage="ESCROW", connector_id="EXIM-A", request_id="REQ-1", operation="release")
    assert verify_chain([first, second])


def test_unified_audit_detects_tampering():
    record = append_record(sequence=1, event="DENY", change_id="REQ-2", owner_id="OWNER-001", decision="DENY", stage="CONNECTOR", connector_id="EXIM-A", request_id="REQ-2", operation="dispatch", trinity={"trust": False, "transparency": True, "performance": True})
    tampered = record.__class__(sequence=record.sequence, timestamp=record.timestamp, event="ALLOW", change_id=record.change_id, owner_id=record.owner_id, decision=record.decision, previous_hash=record.previous_hash, record_hash=record.record_hash, stage=record.stage, connector_id=record.connector_id, request_id=record.request_id, operation=record.operation, trinity=record.trinity)
    assert not verify_chain([tampered])


def test_execution_proof_fields_are_hashed_as_audit_context():
    first = append_record(sequence=1, event="SETTLE", change_id="TX-1", owner_id="OWNER-001", decision="ALLOW", stage="SETTLEMENT", witness_state_root="STATE-1", settlement_hash="SETTLE-1", trinity={"trust": True, "transparency": True, "performance": True})
    second = append_record(sequence=2, event="RECOVER", change_id="REC-1", owner_id="OWNER-001", decision="ALLOW", stage="RECOVERY", previous_hash=first.record_hash, witness_state_root="STATE-1", settlement_hash="SETTLE-1", recovery_decision_hash="REC-DEC-1", trinity={"trust": True, "transparency": True, "performance": True})
    third = append_record(sequence=3, event="RELEASE", change_id="REL-1", owner_id="OWNER-001", decision="ALLOW", stage="RELEASE", previous_hash=second.record_hash, witness_state_root="STATE-1", settlement_hash="SETTLE-1", recovery_decision_hash="REC-DEC-1", execution_chain_hash="CHAIN-1", trinity={"trust": True, "transparency": True, "performance": True})
    assert verify_chain([first, second, third])
    tampered = third.__class__(**{**vars(third), "settlement_hash": "TAMPERED"})
    assert not verify_chain([first, second, tampered])
