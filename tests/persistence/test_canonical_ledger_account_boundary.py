from datetime import timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, PostgreSQLAtomicLedger


def _factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    AtomicLedgerBase.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def test_account_creation_is_rollback_safe():
    engine, sf = _factory()
    ledger = PostgreSQLAtomicLedger(sf)
    with sf() as session:
        result = ledger.create_account_in_transaction(session, "alice", "USD", 100)
        assert result["replayed"] is False
        assert session.get(LedgerAccountModel, "alice").balance == 100
        session.rollback()
    with sf() as session:
        assert session.get(LedgerAccountModel, "alice") is None
    engine.dispose()


def test_account_creation_is_canonical_and_idempotent():
    engine, sf = _factory()
    ledger = PostgreSQLAtomicLedger(sf)
    result = ledger.create_account("alice", "USD", 100)
    assert result["replayed"] is False
    replay = ledger.create_account("alice", "USD", 100)
    assert replay["replayed"] is True
    with sf() as session:
        row = session.get(LedgerAccountModel, "alice")
        assert row.currency == "USD"
        assert row.balance == 100
        assert row.version == 0
        assert row.updated_at.tzinfo is not None or row.updated_at is not None
    engine.dispose()


def test_account_creation_rejects_different_canonical_state():
    engine, sf = _factory()
    ledger = PostgreSQLAtomicLedger(sf)
    ledger.create_account("alice", "USD", 100)
    with pytest.raises(ValueError, match="different canonical state"):
        ledger.create_account("alice", "USD", 101)
    with pytest.raises(ValueError, match="different canonical state"):
        ledger.create_account("alice", "MNT", 100)
    engine.dispose()


def test_account_creation_rejects_negative_initial_balance():
    engine, sf = _factory()
    ledger = PostgreSQLAtomicLedger(sf)
    with pytest.raises(ValueError, match="cannot be negative"):
        ledger.create_account("alice", "USD", -1)
    engine.dispose()
