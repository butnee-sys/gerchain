from network.key_protection import WitnessKey


def test_key_generation():
    key = WitnessKey.generate()

    assert isinstance(key, WitnessKey)
    assert len(key.public_id()) == 64


def test_sign_and_verify():
    key = WitnessKey.generate()
    payload = b"GerChain V84.0 test payload"

    signature = key.sign(payload)

    assert isinstance(signature, str)
    assert len(signature) == 64
    assert key.verify(payload, signature) is True


def test_tampered_payload_rejected():
    key = WitnessKey.generate()

    payload = b"original payload"
    signature = key.sign(payload)

    tampered_payload = b"tampered payload"

    assert key.verify(
        tampered_payload,
        signature,
    ) is False


def test_tampered_signature_rejected():
    key = WitnessKey.generate()

    payload = b"GerChain payload"
    signature = key.sign(payload)

    tampered_signature = signature[:-1] + (
        "0" if signature[-1] != "0" else "1"
    )

    assert key.verify(
        payload,
        tampered_signature,
    ) is False


def test_short_private_key_rejected():
    try:
        WitnessKey(b"short")
        assert False
    except ValueError:
        assert True


def test_non_bytes_payload_rejected():
    key = WitnessKey.generate()

    assert key.verify(
        "not bytes",
        "invalid",
    ) is False