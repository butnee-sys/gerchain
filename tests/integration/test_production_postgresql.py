from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


POSTGRES_URL = os.getenv("GERCHAIN_TEST_POSTGRES_URL")


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="set GERCHAIN_TEST_POSTGRES_URL to run the real PostgreSQL production re-performance",
)
def test_production_factory_bootstraps_canonical_postgresql_schema():
    engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=POSTGRES_URL,
                escrow_id="eai-prod-test-escrow",
                amount=100,
                currency="MNT",
                witness_id="eai-prod-test-witness",
            ),
            engine=engine,
        )
        runtime = factory.build()

        assert runtime.is_canonical_ledger_authoritative
        assert engine.dialect.name == "postgresql"

        tables = set(inspect(engine).get_table_names())
        assert {
            "escrows",
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
            "schema_version",
        }.issubset(tables)
    finally:
        engine.dispose()
