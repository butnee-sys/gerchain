from __future__ import annotations

import os

from sqlalchemy import create_engine, text

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_boots_canonical_postgresql_runtime():
    database_url = os.environ["GERCHAIN_TEST_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="production-boot-escrow",
            amount=100,
            currency="USD",
            witness_id="production-boot-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative is True
    assert runtime.runtime_mode == "production-postgresql"

    with engine.connect() as connection:
        required = {
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "escrows",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
        }
        rows = connection.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = ANY(:names)"
            ),
            {"names": list(required)},
        ).scalars().all()
        assert set(rows) == required

    engine.dispose()
