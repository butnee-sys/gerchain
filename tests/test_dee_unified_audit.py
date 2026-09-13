from dee_security.audit import append_record, verify_chain


def test_unified_audit_chain_covers_governance_execution_context():
    first = append_record(
        sequence=1,
        event="AUTHORIZE",
        change_id="REQ-1",
        owner_id="OWNER-001",
        decision="ALLOW",
        stage="GATEWAY",
        connector_id="EXIM-A",
        request_id="REQ-1",
        operation="release",
    )
    second = append_record(
        sequence=2,
        event="EXECUTE",
        change_id="REQ-1",
        owner_id="OWNER-001",
        decision="ALLOW",
        previous_hash=first.record_hash,
        stage="ESCROW",
        connector_id="EXIM-A",
        request_id="REQ-1",
        operation="release",
    )
    assert verify_chain([first, second])


def test_unified_audit_detects_tampering():
    record = append_record(
        sequence=1,
        event="DENY",
        change_id="REQ-2",
        owner_id="OWNER-001",
        decision="DENY",
        stage="CONNECTOR",
        connector_id="EXIM-A",
        request_id="REQ-2",
        operation="dispatch",
        trinity={"trust": False, "transparency": True, "performance": True},
    )
    tampered = record.__class__(
        sequence=record.sequence,
        timestamp=record.timestamp,
        event="ALLOW",
        change_id=record.change_id,
        owner_id=record.owner_id,
        decision=record.decision,
        previous_hash=record.previous_hash,
        record_hash=record.record_hash,
        stage=record.stage,
        connector_id=record.connector_id,
        request_id=record.request_id,
        operation=record.operation,
        trinity=record.trinity,
    )
    assert not verify_chain([tampered])
