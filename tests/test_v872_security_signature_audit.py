import pytest

from cryptography.hazmat.primitives.asymmetric import ed25519

from network.security_signature_audit import (
    SecuritySignatureAudit,
)


def make_signed_record():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes_raw()

    message = b"gerchain-v87.2-test"
    signature = private_key.sign(message)

    record = {
        "witness_id": "witness-1",
        "message": message,
        "signature": signature,
        "public_key": public_key,
    }

    return private_key, public_key, record


def test_valid_signature_passes():
    _, public_key, record = make_signed_record()

    result = SecuritySignatureAudit.verify_signature(
        record["message"],
        record["signature"],
        public_key,
    )

    assert result["valid"] is True
    assert result["status"] == "PASS"


def test_modified_message_is_rejected():
    _, public_key, record = make_signed_record()

    result = SecuritySignatureAudit.verify_signature(
        b"tampered-message",
        record["signature"],
        public_key,
    )

    assert result["valid"] is False
    assert result["status"] == "REJECTED"


def test_modified_signature_is_rejected():
    _, public_key, record = make_signed_record()

    tampered_signature = bytearray(
        record["signature"]
    )
    tampered_signature[0] ^= 0x01

    result = SecuritySignatureAudit.verify_signature(
        record["message"],
        bytes(tampered_signature),
        public_key,
    )

    assert result["valid"] is False
    assert result["status"] == "REJECTED"


def test_wrong_public_key_is_rejected():
    _, _, record = make_signed_record()

    attacker_private_key = (
        ed25519.Ed25519PrivateKey.generate()
    )
    attacker_public_key = (
        attacker_private_key.public_key().public_bytes_raw()
    )

    result = SecuritySignatureAudit.verify_signature(
        record["message"],
        record["signature"],
        attacker_public_key,
    )

    assert result["valid"] is False
    assert result["status"] == "REJECTED"


def test_signature_record_with_missing_signature_is_inconclusive():
    _, _, record = make_signed_record()

    incomplete_record = dict(record)
    del incomplete_record["signature"]

    result = SecuritySignatureAudit.audit_record(
        incomplete_record
    )

    assert result["status"] == "INCONCLUSIVE"
    assert result["reason"] == "missing_evidence"


def test_signature_record_with_missing_public_key_is_inconclusive():
    _, _, record = make_signed_record()

    incomplete_record = dict(record)
    del incomplete_record["public_key"]

    result = SecuritySignatureAudit.audit_record(
        incomplete_record
    )

    assert result["status"] == "INCONCLUSIVE"
    assert result["reason"] == "missing_evidence"


def test_valid_witness_key_binding_passes():
    _, public_key, record = make_signed_record()

    result = SecuritySignatureAudit.audit_witness_binding(
        record,
        {
            "witness-1": public_key,
        },
    )

    assert result["status"] == "PASS"
    assert result["witness_id"] == "witness-1"


def test_wrong_witness_key_binding_is_rejected():
    _, _, record = make_signed_record()

    other_private_key = (
        ed25519.Ed25519PrivateKey.generate()
    )
    other_public_key = (
        other_private_key.public_key().public_bytes_raw()
    )

    result = SecuritySignatureAudit.audit_witness_binding(
        record,
        {
            "witness-1": other_public_key,
        },
    )

    assert result["status"] == "REJECTED"
    assert (
        result["reason"]
        == "public_key_binding_mismatch"
    )


def test_unknown_witness_is_rejected():
    _, public_key, record = make_signed_record()

    record["witness_id"] = "witness-attacker"

    result = SecuritySignatureAudit.audit_witness_binding(
        record,
        {
            "witness-1": public_key,
        },
    )

    assert result["status"] == "REJECTED"
    assert result["reason"] == "unknown_witness"


def test_full_signature_audit_requires_valid_signature_and_binding():
    _, public_key, record = make_signed_record()

    result = SecuritySignatureAudit.audit(
        record,
        {
            "witness-1": public_key,
        },
    )

    assert result["signature"]["status"] == "PASS"
    assert result["binding"]["status"] == "PASS"
    assert result["status"] == "PASS"