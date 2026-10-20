import pytest

from services.gerchain_runtime import GerchainRuntime


def _production_without_canonical_authority():
    runtime = GerchainRuntime(
        escrow_id="escrow-s2-fallback",
        amount=10,
        currency="MNT",
        witness_id="witness-s2-fallback",
    )
    # Simulate production mode selected but canonical persistence not attached.
    runtime.runtime_mode = "production-postgresql"
    return runtime


@pytest.mark.parametrize(
    "operation",
    [
        "create_account",
        "get_balance",
        "get_escrow_state",
        "fund",
        "lock",
        "release",
        "refund",
        "cancel",
        "settle",
        "create_escrow",
    ],
)
def test_production_mode_never_falls_back_to_memory(operation):
    runtime = _production_without_canonical_authority()
    before = dict(runtime.money_ledger.balances)

    if operation == "create_account":
        invoke = lambda: runtime.create_account("attacker", 100)
    elif operation == "get_balance":
        invoke = lambda: runtime.get_balance("attacker")
    elif operation == "get_escrow_state":
        invoke = runtime.get_escrow_state
    elif operation == "fund":
        invoke = lambda: runtime.fund("tx-fund", "source", "now", {"test": True})
    elif operation == "lock":
        invoke = lambda: runtime.lock("tx-lock", "now", {"test": True})
    elif operation == "release":
        invoke = lambda: runtime.release(
            transaction_id="tx-release",
            destination="beneficiary",
            timestamp="now",
            evidence={"test": True},
            root=object(),
            owner_id="owner",
            authorized=True,
            evidence_verified=True,
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )
    elif operation == "refund":
        invoke = lambda: runtime.refund(
            transaction_id="tx-refund",
            destination="source",
            timestamp="now",
            evidence={"test": True},
            root=object(),
            owner_id="owner",
            authorized=True,
            evidence_verified=True,
            trinity_proof={"trust": True, "transparency": True, "performance": True},
        )
    elif operation == "cancel":
        invoke = lambda: runtime.cancel(
            transaction_id="tx-cancel", timestamp="now", evidence={"test": True}
        )
    elif operation == "settle":
        invoke = lambda: runtime.settle(
            transaction_id="tx-settle",
            source="source",
            destination="destination",
            amount=1,
            currency="MNT",
        )
    else:
        invoke = lambda: runtime.create_escrow(
            escrow_id="new-escrow",
            sender="source",
            beneficiary="beneficiary",
            refund_destination="source",
            amount=1,
            currency="MNT",
        )

    with pytest.raises(RuntimeError):
        invoke()

    assert runtime.money_ledger.balances == before
