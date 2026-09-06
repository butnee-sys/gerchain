from network.chain_tip_recovery import ChainTipRecovery


def test_state_hash_is_deterministic():
    state = {"balance": 100, "status": "LOCKED"}

    first = ChainTipRecovery.state_hash(state)
    second = ChainTipRecovery.state_hash(state)

    assert first == second


def test_chain_tip_is_deterministic():
    state = {"balance": 100, "status": "LOCKED"}

    first = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
    )

    second = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
    )

    assert first == second


def test_chain_tip_verification_passes():
    state = {"balance": 100, "status": "LOCKED"}

    chain_tip = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
    )

    assert ChainTipRecovery.verify_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
        chain_tip,
    ) is True


def test_chain_tip_mismatch_is_rejected():
    state = {"balance": 100, "status": "LOCKED"}

    chain_tip = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
    )

    assert ChainTipRecovery.verify_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
        "invalid-chain-tip",
    ) is False


def test_recovery_validates_trusted_chain_tip():
    state = {
        "balance": 250,
        "status": "LOCKED",
        "sequence": 10,
    }

    trusted_tip = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
    )

    result = ChainTipRecovery.recover(
        "manifest-A",
        10,
        state,
        "root-A",
        trusted_tip,
    )

    assert result["status"] == "VALID"
    assert result["chain_tip_valid"] is True


def test_recovery_rejects_wrong_chain_tip():
    state = {"balance": 250, "status": "LOCKED"}

    result = ChainTipRecovery.recover(
        "manifest-A",
        10,
        state,
        "root-A",
        "wrong-tip",
    )

    assert result["status"] == "REJECTED"
    assert result["chain_tip_valid"] is False


def test_tampered_state_changes_chain_tip():
    original_state = {"balance": 250, "status": "LOCKED"}
    tampered_state = {"balance": 999, "status": "LOCKED"}

    trusted_tip = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        original_state,
        "root-A",
    )

    assert ChainTipRecovery.verify_chain_tip(
        "manifest-A",
        10,
        tampered_state,
        "root-A",
        trusted_tip,
    ) is False


def test_changed_sequence_changes_chain_tip():
    state = {"balance": 250, "status": "LOCKED"}

    first = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
    )

    second = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        11,
        state,
        "root-A",
    )

    assert first != second


def test_changed_state_root_changes_chain_tip():
    state = {"balance": 250, "status": "LOCKED"}

    first = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        state,
        "root-A",
    )

    second = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        10,
        state,
        "root-B",
    )

    assert first != second


def test_recovery_result_contains_integrity_fields():
    state = {"balance": 500, "status": "LOCKED"}

    trusted_tip = ChainTipRecovery.compute_chain_tip(
        "manifest-A",
        20,
        state,
        "root-A",
    )

    result = ChainTipRecovery.recover(
        "manifest-A",
        20,
        state,
        "root-A",
        trusted_tip,
    )

    assert result["version"] == "V85.3"
    assert result["computed_chain_tip"] == trusted_tip
    assert result["trusted_chain_tip"] == trusted_tip
    assert result["chain_tip_valid"] is True