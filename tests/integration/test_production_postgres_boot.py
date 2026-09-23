from __future__ import annotations

import os

from sqlalchemy import create_engine, inspect, text

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_bootstraps_postgresql_schema() -> None:
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)
    config = ProductionRuntimeConfig(
        database_url=database_url,
        escrow_id="integration-escrow",
        amount=100,
        currency="MNT",
        witness_id="integration-witness",
    )
    try:
        factory = ProductionRuntimeFactory(config, engine=engine)
        runtime = factory.create()
        assert runtime.is_canonical_ledger_authoritative

        runtime2 = factory.create()
        assert runtime2.is_canonical_ledger_authoritative

        tables = set(inspect(engine).get_table_names())
        required = {
            "schema_version",
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "escrows",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
        }
        missing = required - tables
        assert not missing, f"missing production tables: {sorted(missing)}"

        with engine.connect() as conn:
            applied = conn.execute(
                text("SELECT count(*) FROM schema_version")
            ).scalar_one()
            assert applied > 0
    finally:
        engine.dispose()
