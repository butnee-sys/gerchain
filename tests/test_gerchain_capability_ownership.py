from services.gerchain_runtime import GerchainRuntime


def test_runtime_has_one_authoritative_value_flow_stack():
    runtime = GerchainRuntime(
        escrow_id="CAPABILITY-AUDIT-001",
        amount=100,
        currency="MNT",
        witness_id="WITNESS-CAPABILITY-001",
        initial_money_state={
            "currency": "MNT",
            "balances": {"BUYER": 100, "ESCROW-CAPABILITY-AUDIT-001": 0},
        },
    )

    assert runtime.money_engine.ledger is runtime.money_ledger
    assert runtime.money_engine.escrow is runtime.escrow_engine
    assert runtime.escrow_service.escrow_engine is runtime.escrow_engine
    assert runtime.escrow_service.money_engine is runtime.money_engine
    assert runtime.escrow_service.verifier is runtime.verifier
    assert runtime.escrow_service.idempotency is runtime.idempotency


def test_runtime_policy_capabilities_do_not_replace_authoritative_engines():
    runtime = GerchainRuntime(
        escrow_id="CAPABILITY-AUDIT-002",
        amount=100,
        currency="MNT",
        witness_id="WITNESS-CAPABILITY-002",
        initial_money_state={
            "currency": "MNT",
            "balances": {"BUYER": 100, "ESCROW-CAPABILITY-AUDIT-002": 0},
        },
    )

    # Policy capabilities constrain or reserve value; they do not own money
    # movement or escrow state transitions.
    assert runtime.holds is not runtime.money_engine
    assert runtime.limits is not runtime.money_engine
    assert runtime.idempotency is not runtime.money_engine
    assert runtime.holds is not runtime.escrow_engine
    assert runtime.limits is not runtime.escrow_engine


def test_runtime_exposes_single_postgres_release_authority_slot():
    runtime = GerchainRuntime(
        escrow_id="CAPABILITY-AUDIT-003",
        amount=100,
        currency="MNT",
        witness_id="WITNESS-CAPABILITY-003",
    )

    assert runtime._postgres_release is None
    assert runtime.is_postgresql_authoritative is False
