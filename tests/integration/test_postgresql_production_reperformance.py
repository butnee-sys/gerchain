from __future__ import annotations

import os

import pytest
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_establishes_canonical_ledger_authority():
    url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    if not url.startswith("postgresql"):
        pytest.fail("production re-performance requires PostgreSQL")

    engine = create_engine(url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="production-reperf-escrow",
            amount=100,
            currency="USD",
            witness_id="production-reperf-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    with engine.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' "
                    "AND tablename IN ("
                    "'gerchain_ledger_accounts', "
                    "'gerchain_ledger_movements', "
                    "'escrows', "
                    "'gerchain_transaction_witnesses', "
                    "'gerchain_outbox_events', "
                    "'gerchain_idempotency_records'"
                    ")"
                )
            )
        }

    assert tables == {
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "escrows",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }
    engine.dispose()
