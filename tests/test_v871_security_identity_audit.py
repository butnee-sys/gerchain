import pytest

from network.security_identity_audit import (
    SecurityIdentityAudit,
)


def test_authorized_witness_passes():
    result = SecurityIdentityAudit.verify_authorized_identity(
        "witness-1",
        {"witness-1", "witness-2"},
    )

    assert result["authorized"] is True
    assert result["status"] == "PASS"


def test_unauthorized_witness_is_rejected():
    result = SecurityIdentityAudit.verify_authorized_identity(
        "witness-fake",
        {"witness-1", "witness-2"},
    )

    assert result["authorized"] is False
    assert result["status"] == "REJECTED"


def test_identity_normalization_is_deterministic():
    result = SecurityIdentityAudit.verify_authorized_identity(
        "  witness-1  ",
        {"witness-1"},
    )

    assert result["witness_id"] == "witness-1"
    assert result["authorized"] is True
    assert result["status"] == "PASS"


def test_empty_identity_is_rejected():
    with pytest.raises(ValueError):
        SecurityIdentityAudit.verify_authorized_identity(
            "   ",
            {"witness-1"},
        )


def test_non_string_identity_is_rejected():
    with pytest.raises(TypeError):
        SecurityIdentityAudit.verify_authorized_identity(
            123,
            {"witness-1"},
        )


def test_valid_witness_record_passes():
    record = {
        "witness_id": "witness-1",
        "verified": True,
    }

    result = SecurityIdentityAudit.audit_witness_record(
        record,
        {"witness-1", "witness-2"},
    )

    assert result["authorized"] is True
    assert result["status"] == "PASS"


def test_fake_witness_record_is_rejected():
    record = {
        "witness_id": "witness-attacker",
        "verified": True,
    }

    result = SecurityIdentityAudit.audit_witness_record(
        record,
        {"witness-1", "witness-2"},
    )

    assert result["authorized"] is False
    assert result["status"] == "REJECTED"
    assert result["reason"] == "unauthorized_witness"


def test_missing_witness_identity_is_inconclusive():
    record = {
        "verified": True,
    }

    result = SecurityIdentityAudit.audit_witness_record(
        record,
        {"witness-1"},
    )

    assert result["status"] == "INCONCLUSIVE"
    assert result["reason"] == "witness_id_missing"


def test_duplicate_witness_identity_is_rejected():
    result = SecurityIdentityAudit.detect_duplicate_identities(
        [
            "witness-1",
            "witness-2",
            "witness-1",
        ]
    )

    assert result["total"] == 3
    assert result["unique"] == 2
    assert result["duplicates"] == ["witness-1"]
    assert result["status"] == "REJECTED"


def test_network_identity_audit_rejects_fake_and_duplicate():
    records = [
        {"witness_id": "witness-1"},
        {"witness_id": "witness-2"},
        {"witness_id": "witness-1"},
        {"witness_id": "witness-fake"},
    ]

    result = SecurityIdentityAudit.audit_network(
        records,
        {"witness-1", "witness-2"},
    )

    assert result["total_records"] == 4
    assert result["rejected"] == 1
    assert (
        result["duplicate_identity_check"]["status"]
        == "REJECTED"
    )
    assert result["status"] == "REJECTED"