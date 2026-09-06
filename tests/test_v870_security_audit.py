import pytest

from network.security_audit import SecurityAudit


def test_canonical_json_is_deterministic():
    first = SecurityAudit.canonical_json(
        {"b": 2, "a": 1}
    )
    second = SecurityAudit.canonical_json(
        {"a": 1, "b": 2}
    )

    assert first == second


def test_state_hash_is_deterministic():
    state = {
        "sequence": 870,
        "balance": 1_000_000,
        "status": "ACTIVE",
    }

    first = SecurityAudit.state_hash(state)
    second = SecurityAudit.state_hash(state)

    assert first == second
    assert len(first) == 64


def test_valid_state_integrity_passes():
    state = {
        "sequence": 870,
        "balance": 1_000_000,
        "status": "ACTIVE",
    }

    expected_hash = SecurityAudit.state_hash(state)

    result = SecurityAudit.verify_state_integrity(
        state,
        expected_hash,
    )

    assert result["matches"] is True
    assert result["status"] == "PASS"


def test_tampered_state_is_rejected():
    state = {
        "sequence": 870,
        "balance": 1_000_000,
        "status": "ACTIVE",
    }

    expected_hash = SecurityAudit.state_hash(state)

    tampered_state = dict(state)
    tampered_state["balance"] = 2_000_000

    result = SecurityAudit.verify_state_integrity(
        tampered_state,
        expected_hash,
    )

    assert result["matches"] is False
    assert result["status"] == "REJECTED"


def test_valid_identity_event_passes():
    result = SecurityAudit.audit_event(
        "IDENTITY",
        "VALID",
        {"witness_id": "witness-1"},
    )

    assert result["category"] == "IDENTITY"
    assert result["decision"] == "PASS"


def test_violation_event_is_rejected():
    result = SecurityAudit.audit_event(
        "AUTHORIZATION",
        "VIOLATION",
        {"authorized": False},
    )

    assert result["category"] == "AUTHORIZATION"
    assert result["decision"] == "REJECTED"


def test_unknown_event_is_inconclusive():
    result = SecurityAudit.audit_event(
        "NETWORK",
        "UNKNOWN",
        {"evidence_available": False},
    )

    assert result["decision"] == "INCONCLUSIVE"


def test_invalid_security_category_is_rejected():
    with pytest.raises(ValueError):
        SecurityAudit.audit_event(
            "UNKNOWN_CATEGORY",
            "VALID",
        )


def test_audit_summary_prioritizes_rejection():
    events = [
        SecurityAudit.audit_event(
            "IDENTITY",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "SIGNATURE",
            "VIOLATION",
        ),
        SecurityAudit.audit_event(
            "REPLAY",
            "UNKNOWN",
        ),
    ]

    result = SecurityAudit.summarize(events)

    assert result["total_events"] == 3
    assert result["passed"] == 1
    assert result["rejected"] == 1
    assert result["inconclusive"] == 1
    assert result["status"] == "REJECTED"


def test_all_valid_events_pass():
    events = [
        SecurityAudit.audit_event(
            "IDENTITY",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "AUTHORIZATION",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "SIGNATURE",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "REPLAY",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "STATE_TAMPERING",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "CHAIN_TIP",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "ANCHOR",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "QUORUM",
            "VALID",
        ),
        SecurityAudit.audit_event(
            "NETWORK",
            "VALID",
        ),
    ]

    result = SecurityAudit.summarize(events)

    assert result["total_events"] == 9
    assert result["passed"] == 9
    assert result["rejected"] == 0
    assert result["inconclusive"] == 0
    assert result["status"] == "PASS"