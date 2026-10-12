from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from persistence.atomic_ledger import LedgerAccountModel, LedgerMovementModel, PostgreSQLAtomicLedger
from services.gerchain_runtime_factory import initialize_canonical_postgres_schema


DATABASE_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="requires real PostgreSQL via GERCHAIN_TEST_DATABASE_URL")
def test_canonical_migrations_and_concurrent_ledger_contention():
    """Run migrations on PostgreSQL, then prove competing spends serialize safely."""
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        initialize_canonical_postgres_schema(engine)
        sessions = sessionmaker(bind=engine, expire_on_commit=False)
        token = uuid.uuid4().hex
        source, dest_a, dest_b = (f"ea35-{token}-{name}" for name in ("source", "a", "b"))

        with sessions() as session:
            session.add_all(
                [
                    LedgerAccountModel(account_id=source, currency="TST", balance=100, version=0),
                    LedgerAccountModel(account_id=dest_a, currency="TST", balance=0, version=0),
                    LedgerAccountModel(account_id=dest_b, currency="TST", balance=0, version=0),
                ]
            )
            session.commit()

        def spend(destination: str, transaction_id: str):
            with sessions() as session:
                try:
                    result = PostgreSQLAtomicLedger.transfer_in_transaction(
                        session,
                        transaction_id=transaction_id,
                        source=source,
                        destination=destination,
                        amount=70,
                        currency="TST",
                    )
                    session.commit()
                    return ("ok", result)
                except ValueError as exc:
                    session.rollback()
                    if "insufficient" in str(exc).lower() or "balance" in str(exc).lower():
                        return ("insufficient", str(exc))
                    raise

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(spend, dest_a, f"ea35-{token}-tx-a"),
                pool.submit(spend, dest_b, f"ea35-{token}-tx-b"),
            ]
            results = [future.result(timeout=30) for future in futures]

        assert sorted(result[0] for result in results) == ["insufficient", "ok"]

        with sessions() as session:
            accounts = {
                row.account_id: row
                for row in session.execute(
                    select(LedgerAccountModel).where(
                        LedgerAccountModel.account_id.in_([source, dest_a, dest_b])
                    )
                ).scalars()
            }
            movements = session.execute(
                select(LedgerMovementModel).where(
                    LedgerMovementModel.transaction_id.in_(
                        [f"ea35-{token}-tx-a", f"ea35-{token}-tx-b"]
                    )
                )
            ).scalars().all()
            assert accounts[source].balance == 30
            assert accounts[dest_a].balance + accounts[dest_b].balance == 70
            assert len(movements) == 1
            assert sum(1 for row in movements if row.amount == 70 and row.currency == "TST") == 1
    finally:
        engine.dispose()
