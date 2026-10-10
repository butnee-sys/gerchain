import pytest

from services.gerchain_runtime import GerchainRuntime


def _legacy_postgres_runtime():
    runtime = GerchainRuntime(
        escrow_id="escrow-1",
        amount=10,
        currency="MNT",
        witness_id="witness-1",
    )
    # This represents the old PostgreSQL-release-only configuration: it is not
    # allowed to fall back to MoneyLedger for any production-facing operation.
    runtime.configure_postgres_release(lambda: None)
    return runtime


@pytest.mark.parametrize(
    ("operation", "invoke"),
    [
        ("FUND", lambda r: r.fund("tx-1", "source", "t", {"e": 1})),
        ("LOCK", lambda r: r.lock("tx-1", "t", {"e": 1})),
        ("CREATE_ACCOUNT", lambda r: r.create_account("account-1", 100)),
        ("BALANCE_READ", lambda r: r.get_balance("account-1")),
        ("ESCROW_READ", lambda r: r.get_escrow_state()),
        ("CREATE_HOLD", lambda r: r.create_hold(hold_id="h-1", account_id="a-1", amount=1)),
    ],
)
def test_production_release_only_runtime_fails_closed_instead_of_using_memory(operation, invoke):
    runtime = _legacy_postgres_runtime()

    with pytest.raises(RuntimeError, match=f"{operation} requires Canonical Ledger authority"):
        invoke(runtime)
