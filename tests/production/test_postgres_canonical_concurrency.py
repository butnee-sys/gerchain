from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger


@pytest.mark.integration
def test_canonical_ledger_concurrent_same_transaction_replays_once():
    url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    engine = create_engine(url, pool_pre_ping=True)
    PostgreSQLAtomicLedger.initialize_schema(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE TABLE gerchain_ledger_movements, gerchain_ledger_accounts CASCADE"
        )

    with Session() as session:
        ledger = PostgreSQLAtomicLedger(Session)
        ledger.create_account_in_transaction(session, "CONC-SOURCE", "MNT", 1000)
        ledger.create_account_in_transaction(session, "CONC-DEST", "MNT", 0)
        session.commit()

    def worker(index: int):
        with Session() as session:
            try:
                result = PostgreSQLAtomicLedger.transfer_in_transaction(
                    session,
                    transaction_id="CONC-SAME-TX",
                    source="CONC-SOURCE",
                    destination="CONC-DEST",
                    amount=100,
                    currency="MNT",
                    operation="FUND",
                    escrow_id="CONC-ESCROW",
                    integrity_hash="concurrency-proof",
                )
                session.commit()
                return result["replayed"]
            except Exception:
                session.rollback()
                raise

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(worker, range(20)))

    with Session() as session:
        source = session.get(LedgerAccountModel, "CONC-SOURCE")
        destination = session.get(LedgerAccountModel, "CONC-DEST")
        movements = list(session.execute(select(LedgerMovementModel)).scalars())

        assert results.count(False) == 1
        assert results.count(True) == 19
        assert len(movements) == 1
        assert source.balance == 900
        assert destination.balance == 100
        assert movements[0].transaction_id == "CONC-SAME-TX"

    engine.dispose()
