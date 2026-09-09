from services.gerchain_runtime import GerchainRuntime


def build_runtime():
    runtime = GerchainRuntime(
        escrow_id="ESCROW-RUNTIME-001",
        amount=1_000_000,
        currency="MNT",
        witness_id="WITNESS-RUNTIME-001",
        initial_money_state={
            "currency": "MNT",
            "balances": {
                "BUYER": 2_000_000,
                "ESCROW-RUNTIME-001": 0,
                "SELLER": 0,
            },
        },
    )

    runtime.create_account(
        "BUYER",
        2_000_000,
    )

    runtime.create_account(
        "ESCROW-RUNTIME-001",
        0,
    )

    runtime.create_account(
        "SELLER",
        0,
    )

    return runtime


def test_runtime_constructs_core():
    runtime = build_runtime()

    assert runtime.get_escrow_state()["state"] == "CREATED"

    assert runtime.get_balance("BUYER") == 2_000_000
    assert runtime.get_balance("ESCROW-RUNTIME-001") == 0
    assert runtime.get_balance("SELLER") == 0


def test_runtime_full_escrow_lifecycle():
    runtime = build_runtime()

    runtime.fund(
        transaction_id="TX-FUND-001",
        source="BUYER",
        timestamp="2026-09-08T10:00:00Z",
        evidence={
            "type": "FUNDING",
            "reference": "TEST-FUND-001",
        },
    )

    assert (
        runtime.get_escrow_state()["state"]
        == "FUNDED"
    )

    assert runtime.get_balance("BUYER") == 1_000_000
    assert (
        runtime.get_balance("ESCROW-RUNTIME-001")
        == 1_000_000
    )

    runtime.lock(
        transaction_id="TX-LOCK-001",
        timestamp="2026-09-08T10:01:00Z",
        evidence={
            "type": "LOCK",
            "reference": "TEST-LOCK-001",
        },
    )

    assert (
        runtime.get_escrow_state()["state"]
        == "LOCKED"
    )

    runtime.release(
        transaction_id="TX-RELEASE-001",
        destination="SELLER",
        timestamp="2026-09-08T10:02:00Z",
        evidence={
            "type": "RELEASE",
            "reference": "TEST-RELEASE-001",
        },
    )

    assert (
        runtime.get_escrow_state()["state"]
        == "RELEASED"
    )

    assert runtime.get_balance("BUYER") == 1_000_000
    assert (
        runtime.get_balance("ESCROW-RUNTIME-001")
        == 0
    )
    assert runtime.get_balance("SELLER") == 1_000_000


def test_runtime_bundle_is_independently_verified():
    runtime = build_runtime()

    runtime.fund(
        transaction_id="TX-FUND-002",
        source="BUYER",
        timestamp="2026-09-08T11:00:00Z",
        evidence={
            "type": "FUNDING",
            "reference": "TEST-FUND-002",
        },
    )

    runtime.lock(
        transaction_id="TX-LOCK-002",
        timestamp="2026-09-08T11:01:00Z",
        evidence={
            "type": "LOCK",
            "reference": "TEST-LOCK-002",
        },
    )

    runtime.release(
        transaction_id="TX-RELEASE-002",
        destination="SELLER",
        timestamp="2026-09-08T11:02:00Z",
        evidence={
            "type": "RELEASE",
            "reference": "TEST-RELEASE-002",
        },
    )

    assert runtime.verify() is True

    report = runtime.verify_report()

    assert report["witness_cryptographic"] is True
    assert report["escrow_semantic"] is True
    assert report["money_semantic"] is True
    assert report["overall"] is True


def test_runtime_witness_sequence_is_authoritative():
    runtime = build_runtime()

    runtime.fund(
        transaction_id="TX-FUND-003",
        source="BUYER",
        timestamp="2026-09-08T12:00:00Z",
        evidence={
            "type": "FUNDING",
            "reference": "TEST-FUND-003",
        },
    )

    runtime.lock(
        transaction_id="TX-LOCK-003",
        timestamp="2026-09-08T12:01:00Z",
        evidence={
            "type": "LOCK",
            "reference": "TEST-LOCK-003",
        },
    )

    runtime.release(
        transaction_id="TX-RELEASE-003",
        destination="SELLER",
        timestamp="2026-09-08T12:02:00Z",
        evidence={
            "type": "RELEASE",
            "reference": "TEST-RELEASE-003",
        },
    )

    entries = runtime.witness_chain.entries

    # V80.4.3: Initial money state is an authoritative genesis witness event.
    # The complete lifecycle therefore contains six canonical witness entries.
    assert len(entries) == 6

    expected_events = [
        (1, "INITIAL_MONEY_STATE"),
        (2, "MONEY_TRANSFER"),
        (3, "ESCROW_TRANSITION"),
        (4, "ESCROW_TRANSITION"),
        (5, "ATOMIC_SETTLEMENT"),
        (6, "ESCROW_TRANSITION"),
    ]

    assert [
        (entry.record.sequence, entry.record.event_type)
        for entry in entries
    ] == expected_events

    assert runtime.verify() is True


def test_runtime_invalid_lifecycle_is_rejected():
    runtime = build_runtime()

    try:
        runtime.release(
            transaction_id="TX-INVALID-001",
            destination="SELLER",
            timestamp="2026-09-08T13:00:00Z",
            evidence={
                "type": "INVALID",
            },
        )
    except ValueError as exc:
        assert "LOCKED" in str(exc)
    else:
        raise AssertionError(
            "Invalid RELEASE must be rejected."
        )


def test_runtime_initial_money_state_matches_ledger():
    runtime = build_runtime()

    authoritative = (
        runtime.witness_chain
        .get_initial_money_commitment()
    )

    assert authoritative is not None
    assert authoritative["state"]["currency"] == "MNT"
    assert authoritative["state"]["balances"] == {
        "BUYER": 2_000_000,
        "ESCROW-RUNTIME-001": 0,
        "SELLER": 0,
    }

    assert runtime.money_ledger.currency == "MNT"
    assert runtime.money_ledger.balances == (
        authoritative["state"]["balances"]
    )


def test_runtime_initial_money_state_mismatch_is_detected():
    runtime = build_runtime()

    runtime.money_ledger.balances["BUYER"] = 1_900_000

    authoritative = (
        runtime.witness_chain
        .get_initial_money_commitment()
    )

    assert authoritative is not None
    assert runtime.money_ledger.balances != (
        authoritative["state"]["balances"]
    )


def test_runtime_initial_money_state_extra_account_is_detected():
    runtime = build_runtime()

    runtime.money_ledger.create_account(
        "UNAUTHORIZED-ACCOUNT",
        500_000,
    )

    authoritative = (
        runtime.witness_chain
        .get_initial_money_commitment()
    )

    assert authoritative is not None
    assert set(runtime.money_ledger.balances) != set(
        authoritative["state"]["balances"]
    )


def test_runtime_initial_money_state_currency_mismatch_is_detected():
    runtime = build_runtime()

    runtime.money_ledger.currency = "USD"

    authoritative = (
        runtime.witness_chain
        .get_initial_money_commitment()
    )

    assert authoritative is not None
    assert runtime.money_ledger.currency != (
        authoritative["state"]["currency"]
    )


def test_runtime_initial_money_consistency_guard_rejects_mismatch():
    runtime = build_runtime()

    runtime.money_ledger.balances["BUYER"] = 1_900_000

    try:
        runtime.verify_initial_money_consistency()
    except ValueError as exc:
        assert "initial money state" in str(exc).lower()
    else:
        raise AssertionError(
            "Runtime must reject initial money state mismatch."
        )
