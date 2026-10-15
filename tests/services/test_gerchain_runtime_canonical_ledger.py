from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase
from services.gerchain_runtime import GerchainRuntime


def _runtime():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    AtomicLedgerBase.metadata.create_all(engine)
    sf = sessionmaker(bind=engine)
    runtime = GerchainRuntime(
        escrow_id="escrow-1",
        amount=10,
        currency="USD",
        witness_id="w-1",
    )
    runtime.configure_canonical_ledger(sf)
    return engine, runtime


def test_production_create_account_and_read_balance_use_canonical_ledger():
    engine, runtime = _runtime()
    runtime.create_account("alice", 125)
    assert runtime.get_balance("alice") == 125
    assert runtime.money_ledger.balances == {}
    engine.dispose()


def test_test_runtime_still_uses_memory_ledger():
    runtime = GerchainRuntime(
        escrow_id="escrow-1",
        amount=10,
        currency="USD",
        witness_id="w-1",
    )
    runtime.create_account("alice", 125)
    assert runtime.get_balance("alice") == 125
