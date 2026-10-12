from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect, text

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


@pytest.mark.integration
def test_production_factory_boots_real_postgresql_and_establishes_canonical_authority():
    database_url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL re-performance")

    # The test URL must point at the PostgreSQL service supplied by CI. Do not
    # let a SQLite or other fallback silently count as production evidence.
    engine = create_engine(database_url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="EA35-FACTORY-ESCROW",
            amount=100,
            currency="MNT",
            witness_id="EA35-FACTORY-WITNESS",
        ),
        engine=engine,
    )
    try:
        runtime = factory.create()
        assert engine.dialect.name == "postgresql"
        assert runtime.is_canonical_ledger_authoritative is True
        assert runtime._canonical_ledger is not None
        assert runtime._session_factory is not None

        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
            inspector = inspect(connection)
            assert {
                "gerchain_ledger_accounts",
                "gerchain_ledger_movements",
                "escrows",
                "gerchain_transaction_witnesses",
                "gerchain_outbox_events",
                "gerchain_idempotency_records",
                "schema_version",
            }.issubset(set(inspector.get_table_names()))

            versions = connection.execute(
                text("SELECT version FROM schema_version ORDER BY version")
            ).scalars().all()
            assert versions == list(range(1, 17))

        # The production constructor must not activate the legacy ReleaseAccount
        # authority as a parallel balance truth.
        assert runtime._postgres_release is None
        assert runtime.is_postgresql_authoritative is False
    finally:
        engine.dispose()
