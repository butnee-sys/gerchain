from network.authorization import AuthorizedWitnessRegistry
from network.signed_witness_record import SignedWitnessRecord
from network.witness_identity import WitnessIdentity
from network.witness_signature import WitnessSignature


def test_create_signed_record():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    record = SignedWitnessRecord.create(
        identity,
        witness,
        b"GerChain V84.4 payload",
    )

    assert record.identity.node_id == "node-001"
    assert record.payload == b"GerChain V84.4 payload"
    assert len(record.signature) == 64


def test_valid_record_is_accepted():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    record = SignedWitnessRecord.create(
        identity,
        witness,
        b"valid payload",
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    result = record.verify(registry)

    assert result["authorized"] is True
    assert result["identity_valid"] is True
    assert result["signature_valid"] is True
    assert result["accepted"] is True


def test_record_hash_is_deterministic():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    record_a = SignedWitnessRecord.create(
        identity,
        witness,
        b"deterministic payload",
    )

    record_b = SignedWitnessRecord(
        identity,
        b"deterministic payload",
        record_a.signature,
    )

    assert record_a.canonical_payload() == record_b.canonical_payload()
    assert record_a.record_hash() == record_b.record_hash()


def test_tampered_payload_rejected():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    record = SignedWitnessRecord.create(
        identity,
        witness,
        b"original payload",
    )

    record.payload = b"tampered payload"

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    result = record.verify(registry)

    assert result["signature_valid"] is False
    assert result["accepted"] is False


def test_tampered_node_id_rejected():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    record = SignedWitnessRecord.create(
        identity,
        witness,
        b"identity payload",
    )

    record.identity.node_id = "node-002"

    registry = AuthorizedWitnessRegistry(
        ["node-002"]
    )

    result = record.verify(registry)

    assert result["identity_valid"] is True
    assert result["signature_valid"] is False
    assert result["accepted"] is False


def test_tampered_public_key_rejected():
    witness_a = WitnessSignature.generate()
    witness_b = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness_a,
    )

    record = SignedWitnessRecord.create(
        identity,
        witness_a,
        b"public key payload",
    )

    record.identity.public_key = (
        witness_b.public_key_bytes()
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    result = record.verify(registry)

    assert result["signature_valid"] is False
    assert result["accepted"] is False


def test_wrong_signature_rejected():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    record = SignedWitnessRecord.create(
        identity,
        witness,
        b"signature payload",
    )

    record.signature = (
        record.signature[:-1]
        + bytes([record.signature[-1] ^ 1])
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    result = record.verify(registry)

    assert result["signature_valid"] is False
    assert result["accepted"] is False


def test_unauthorized_node_rejected():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    record = SignedWitnessRecord.create(
        identity,
        witness,
        b"authorized identity required",
    )

    registry = AuthorizedWitnessRegistry(
        ["node-999"]
    )

    result = record.verify(registry)

    assert result["authorized"] is False
    assert result["signature_valid"] is True
    assert result["accepted"] is False


def test_serialized_record_contains_integrity_fields():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    record = SignedWitnessRecord.create(
        identity,
        witness,
        b"serialization test",
    )

    data = record.to_dict()

    assert data["version"] == "V84.4"
    assert data["node_id"] == "node-001"
    assert data["public_key"] == witness.public_key_bytes().hex()
    assert data["binding_hash"] == identity.binding_hash()
    assert data["payload"] == b"serialization test".hex()
    assert data["signature"] == record.signature.hex()
    assert data["record_hash"] == record.record_hash()