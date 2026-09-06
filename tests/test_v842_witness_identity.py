from network.witness_identity import WitnessIdentity
from network.witness_signature import WitnessSignature


def test_identity_from_witness():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    assert identity.node_id == "node-001"
    assert identity.public_key == witness.public_key_bytes()


def test_binding_is_deterministic():
    witness = WitnessSignature.generate()

    identity_a = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    identity_b = WitnessIdentity(
        "node-001",
        witness.public_key_bytes(),
    )

    assert identity_a.binding_payload() == identity_b.binding_payload()
    assert identity_a.binding_hash() == identity_b.binding_hash()


def test_different_node_id_changes_binding():
    witness = WitnessSignature.generate()

    identity_a = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    identity_b = WitnessIdentity.from_witness(
        "node-002",
        witness,
    )

    assert identity_a.binding_hash() != identity_b.binding_hash()


def test_different_public_key_changes_binding():
    witness_a = WitnessSignature.generate()
    witness_b = WitnessSignature.generate()

    identity_a = WitnessIdentity.from_witness(
        "node-001",
        witness_a,
    )

    identity_b = WitnessIdentity.from_witness(
        "node-001",
        witness_b,
    )

    assert identity_a.binding_hash() != identity_b.binding_hash()


def test_identity_verifies_signature():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    payload = b"GerChain V84.2 identity test"
    signature = witness.sign(payload)

    assert identity.verify_signature(
        payload,
        signature,
    ) is True


def test_identity_rejects_tampered_payload():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    payload = b"original"
    signature = witness.sign(payload)

    assert identity.verify_signature(
        b"tampered",
        signature,
    ) is False


def test_identity_serialization():
    witness = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    data = identity.to_dict()

    assert data["version"] == "V84.2"
    assert data["node_id"] == "node-001"
    assert data["public_key"] == witness.public_key_bytes().hex()
    assert data["binding_hash"] == identity.binding_hash()


def test_invalid_public_key_length_rejected():
    try:
        WitnessIdentity(
            "node-001",
            b"short",
        )
        assert False
    except ValueError:
        assert True


def test_empty_node_id_rejected():
    witness = WitnessSignature.generate()

    try:
        WitnessIdentity(
            "",
            witness.public_key_bytes(),
        )
        assert False
    except ValueError:
        assert True