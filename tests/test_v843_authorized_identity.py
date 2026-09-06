from network.authorization import AuthorizedWitnessRegistry
from network.authorized_identity import AuthorizedWitnessIdentity
from network.witness_identity import WitnessIdentity
from network.witness_signature import WitnessSignature


def test_authorized_identity_accepts_valid_witness():
    witness = WitnessSignature.generate()
    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    binding = AuthorizedWitnessIdentity(
        registry,
        identity,
    )

    payload = b"GerChain V84.3"
    signature = witness.sign(payload)

    result = binding.verify(
        payload,
        signature,
        identity.binding_hash(),
    )

    assert result["authorized"] is True
    assert result["binding_valid"] is True
    assert result["signature_valid"] is True
    assert result["accepted"] is True


def test_unauthorized_witness_rejected():
    witness = WitnessSignature.generate()
    identity = WitnessIdentity.from_witness(
        "node-unauthorized",
        witness,
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    binding = AuthorizedWitnessIdentity(
        registry,
        identity,
    )

    payload = b"unauthorized witness"
    signature = witness.sign(payload)

    result = binding.verify(
        payload,
        signature,
        identity.binding_hash(),
    )

    assert result["authorized"] is False
    assert result["signature_valid"] is False
    assert result["accepted"] is False


def test_wrong_binding_hash_rejected():
    witness = WitnessSignature.generate()
    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    binding = AuthorizedWitnessIdentity(
        registry,
        identity,
    )

    payload = b"binding test"
    signature = witness.sign(payload)

    result = binding.verify(
        payload,
        signature,
        "0" * 64,
    )

    assert result["authorized"] is True
    assert result["binding_valid"] is False
    assert result["signature_valid"] is False
    assert result["accepted"] is False


def test_tampered_payload_rejected():
    witness = WitnessSignature.generate()
    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    binding = AuthorizedWitnessIdentity(
        registry,
        identity,
    )

    signature = witness.sign(
        b"original payload"
    )

    result = binding.verify(
        b"tampered payload",
        signature,
        identity.binding_hash(),
    )

    assert result["authorized"] is True
    assert result["binding_valid"] is True
    assert result["signature_valid"] is False
    assert result["accepted"] is False


def test_wrong_witness_signature_rejected():
    witness_a = WitnessSignature.generate()
    witness_b = WitnessSignature.generate()

    identity = WitnessIdentity.from_witness(
        "node-001",
        witness_a,
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    binding = AuthorizedWitnessIdentity(
        registry,
        identity,
    )

    payload = b"wrong signer"
    signature = witness_b.sign(payload)

    result = binding.verify(
        payload,
        signature,
        identity.binding_hash(),
    )

    assert result["authorized"] is True
    assert result["binding_valid"] is True
    assert result["signature_valid"] is False
    assert result["accepted"] is False


def test_authorization_and_signature_are_both_required():
    witness = WitnessSignature.generate()
    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    binding = AuthorizedWitnessIdentity(
        registry,
        identity,
    )

    payload = b"complete verification"
    signature = witness.sign(payload)

    assert binding.is_authorized() is True
    assert binding.verify_signature(
        payload,
        signature,
    ) is True


def test_identity_binding_is_required_for_acceptance():
    witness = WitnessSignature.generate()
    identity = WitnessIdentity.from_witness(
        "node-001",
        witness,
    )

    registry = AuthorizedWitnessRegistry(
        ["node-001"]
    )

    binding = AuthorizedWitnessIdentity(
        registry,
        identity,
    )

    payload = b"identity binding"
    signature = witness.sign(payload)

    assert binding.verify(
        payload,
        signature,
        identity.binding_hash(),
    )["accepted"] is True

    assert binding.verify(
        payload,
        signature,
        "f" * 64,
    )["accepted"] is False