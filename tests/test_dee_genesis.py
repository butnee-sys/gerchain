from dee_security.genesis import GenesisError, build_genesis_anchor, verify_genesis_anchor


def test_genesis_is_deterministic():
    first = build_genesis_anchor(owner_id="owner-1", public_key="pk-1", policy_version="1")
    second = build_genesis_anchor(owner_id="owner-1", public_key="pk-1", policy_version="1")
    assert first == second
    assert verify_genesis_anchor(first)


def test_genesis_binds_identity_key_and_policy():
    anchor = build_genesis_anchor(owner_id="owner-1", public_key="pk-1", policy_version="1")
    assert anchor.genesis_hash != build_genesis_anchor(
        owner_id="owner-2", public_key="pk-1", policy_version="1"
    ).genesis_hash
    assert anchor.genesis_hash != build_genesis_anchor(
        owner_id="owner-1", public_key="pk-2", policy_version="1"
    ).genesis_hash
    assert anchor.genesis_hash != build_genesis_anchor(
        owner_id="owner-1", public_key="pk-1", policy_version="2"
    ).genesis_hash


def test_genesis_rejects_tampering():
    anchor = build_genesis_anchor(owner_id="owner-1", public_key="pk-1", policy_version="1")
    tampered = type(anchor)(anchor.owner_id, anchor.public_key, "2", anchor.genesis_hash)
    assert not verify_genesis_anchor(tampered)


def test_genesis_fails_closed_on_missing_fields():
    for kwargs in (
        {"owner_id": "", "public_key": "pk", "policy_version": "1"},
        {"owner_id": "owner", "public_key": "", "policy_version": "1"},
        {"owner_id": "owner", "public_key": "pk", "policy_version": ""},
    ):
        try:
            build_genesis_anchor(**kwargs)
        except GenesisError:
            pass
        else:
            raise AssertionError("missing genesis field must fail closed")
