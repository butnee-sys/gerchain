from __future__ import annotations

import os

from sqlalchemy import create_engine, text

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_runtime_factory_boots_against_postgresql():
    database_url = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(database_url, future=True)

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="escrow-production-test",
            amount=100,
            currency="USD",
            witness_id="witness-production-test",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    with engine.connect() as connection:
        versions = connection.execute(
            text("SELECT version FROM schema_version ORDER BY version")
        ).scalars().all()
        assert versions == list(range(1, 9))

        tables = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT tablename FROM pg_catalog.pg_tables "
                    "WHERE schemaname = 'public'"
                )
            ).all()
        }

    required = {
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "escrows",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }
    assert required <= tables

    engine.dispose()
