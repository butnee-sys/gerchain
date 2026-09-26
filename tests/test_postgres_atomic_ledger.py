import os
import hashlib
import json

import pytest

from persistence.atomic_ledger import AtomicLedgerBase, LedgerAccountModel, PostgreSQLAtomicLedger
from persistence.idempotency_store import build_postgres_session_factory


@pytest.fixture()
def ledger():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    factory = build_postgres_session_factory(url)
    # The shared test database may already contain the idempotency schema.
    from sqlalchemy import create_engine
    engine = create_engine(url, pool_pre_ping=True)
    AtomicLedgerBase.metadata.create_all(engine)
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        from datetime import datetime, timezone
        for account_id, balance in (("PG-SOURCE", 2_000_000), ("PG-DEST", 0)):
            if session.get(LedgerAccountModel, account_id) is None:
                session.add(LedgerAccountModel(account_id=account_id, currency="MNT", balance=balance, version=0, updated_at=datetime.now(timezone.utc)))
        session.commit()
    return PostgreSQLAtomicLedger(factory)


def test_duplicate_transaction_id_moves_value_once(ledger):
    material = json.dumps({
        "transaction_id": "TX-PG-LEDGER-001",
        "operation": "SETTLEMENT",
        "escrow_id": None,
        "source": "PG-SOURCE",
        "destination": "PG-DEST",
        "amount": 100,
        "currency": "MNT",
    }, sort_keys=True, separators=(",", ":"))
    integrity_hash = hashlib.sha256(material.encode()).hexdigest()
    first = ledger.transfer(
        "TX-PG-LEDGER-001", "PG-SOURCE", "PG-DEST", 100, "MNT",
        operation="SETTLEMENT", escrow_id=None, integrity_hash=integrity_hash,
    )
    second = ledger.transfer(
        "TX-PG-LEDGER-001", "PG-SOURCE", "PG-DEST", 100, "MNT",
        operation="SETTLEMENT", escrow_id=None, integrity_hash=integrity_hash,
    )
    assert first["replayed"] is False
    assert second["replayed"] is True
