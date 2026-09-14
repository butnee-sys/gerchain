from dee_security import AuthorizationPolicy
from services.g3_core_handler import G3CoreRuntimeHandler
from services.gerchain_runtime import GerchainRuntime

from tests.test_g3_dee_authorized_handler import AMOUNT, ESCROW_ID, build_signed_release, prepare_locked


def build_runtime():
    runtime = GerchainRuntime(
        escrow_id=ESCROW_ID,
        amount=AMOUNT,
        currency="MNT",
        witness_id="IDEMPOTENCY-WITNESS-001",
        initial_money_state={
            "currency": "MNT",
            "balances": {"INSURER": AMOUNT, ESCROW_ID: 0, "BENEFICIARY": 0, "OTHER": 0},
        },
    )
    runtime.create_account("INSURER", AMOUNT)
    runtime.create_account(ESCROW_ID, 0)
    runtime.create_account("BENEFICIARY", 0)
    runtime.create_account("OTHER", 0)
    return runtime


def test_authoritative_release_replay_does_not_move_value_twice():
    runtime = build_runtime()
    prepare_locked(runtime)
    root, _, _ = build_signed_release()
    proof = {"trust": True, "transparency": True, "performance": True}

    first = runtime.release(
        transaction_id="TX-IDEMP-001",
        destination="BENEFICIARY",
        timestamp="2026-09-14T08:02:00Z",
        evidence={"type": "TEST"},
        root=root,
        owner_id=root.owner_id,
        authorized=True,
        evidence_verified=True,
        trinity_proof=proof,
    )
    replay = runtime.release(
        transaction_id="TX-IDEMP-001",
        destination="BENEFICIARY",
        timestamp="2026-09-14T08:02:00Z",
        evidence={"type": "TEST"},
        root=root,
        owner_id=root.owner_id,
        authorized=True,
        evidence_verified=True,
        trinity_proof=proof,
    )

    assert replay == first
    assert runtime.get_balance("BENEFICIARY") == AMOUNT
    assert runtime.get_balance(ESCROW_ID) == 0
    assert len(runtime.money_engine.records) == 1


def test_authoritative_release_key_conflict_is_denied():
    runtime = build_runtime()
    prepare_locked(runtime)
    root, _, _ = build_signed_release()
    proof = {"trust": True, "transparency": True, "performance": True}

    runtime.release(
        transaction_id="TX-IDEMP-002",
        destination="BENEFICIARY",
        timestamp="2026-09-14T08:02:00Z",
        evidence={"type": "TEST"},
        root=root,
        owner_id=root.owner_id,
        authorized=True,
        evidence_verified=True,
        trinity_proof=proof,
    )

    try:
        runtime.release(
            transaction_id="TX-IDEMP-002",
            destination="OTHER",
            timestamp="2026-09-14T08:03:00Z",
            evidence={"type": "TEST"},
            root=root,
            owner_id=root.owner_id,
            authorized=True,
            evidence_verified=True,
            trinity_proof=proof,
        )
    except Exception as exc:
        assert "Idempotency" in type(exc).__name__
    else:
        raise AssertionError("same release key with a different destination must be denied")

    assert runtime.get_balance("BENEFICIARY") == AMOUNT
    assert runtime.get_balance("OTHER") == 0
    assert len(runtime.money_engine.records) == 1
