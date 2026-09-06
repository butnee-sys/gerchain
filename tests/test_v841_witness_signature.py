from network.witness_signature import WitnessSignature


def test_key_generation():
    witness = WitnessSignature.generate()

    assert isinstance(witness, WitnessSignature)

    public_key = witness.public_key_bytes()

    assert isinstance(public_key, bytes)
    assert len(public_key) == 32


def test_public_id():
    witness = WitnessSignature.generate()

    public_id = witness.public_id()

    assert isinstance(public_id, str)
    assert len(public_id) == 64


def test_sign_and_independent_verify():
    witness = WitnessSignature.generate()

    payload = b"GerChain V84.1 witness payload"

    signature = witness.sign(payload)
    public_key = witness.public_key_bytes()

    assert isinstance(signature, bytes)
    assert len(signature) == 64

    assert WitnessSignature.verify(
        public_key,
        payload,
        signature,
    ) is True


def test_private_key_not_required_for_verification():
    witness = WitnessSignature.generate()

    payload = b"independent verification"

    signature = witness.sign(payload)
    public_key = witness.public_key_bytes()

    verifier_result = WitnessSignature.verify(
        public_key,
        payload,
        signature,
    )

    assert verifier_result is True


def test_tampered_payload_rejected():
    witness = WitnessSignature.generate()

    payload = b"original payload"
    signature = witness.sign(payload)
    public_key = witness.public_key_bytes()

    tampered_payload = b"tampered payload"

    assert WitnessSignature.verify(
        public_key,
        tampered_payload,
        signature,
    ) is False


def test_tampered_signature_rejected():
    witness = WitnessSignature.generate()

    payload = b"GerChain payload"
    signature = witness.sign(payload)
    public_key = witness.public_key_bytes()

    tampered_signature = (
        signature[:-1]
        + bytes([signature[-1] ^ 1])
    )

    assert WitnessSignature.verify(
        public_key,
        payload,
        tampered_signature,
    ) is False


def test_wrong_public_key_rejected():
    witness_a = WitnessSignature.generate()
    witness_b = WitnessSignature.generate()

    payload = b"witness A payload"

    signature = witness_a.sign(payload)

    assert WitnessSignature.verify(
        witness_b.public_key_bytes(),
        payload,
        signature,
    ) is False


def test_wrong_payload_type_rejected():
    witness = WitnessSignature.generate()

    signature = witness.sign(b"valid payload")
    public_key = witness.public_key_bytes()

    assert WitnessSignature.verify(
        public_key,
        "not bytes",
        signature,
    ) is False