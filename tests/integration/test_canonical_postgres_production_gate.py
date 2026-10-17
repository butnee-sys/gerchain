from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


@pytest.mark.postgres_integration
def test_empty_postgres_database_migrates_and_boots_canonical_runtime():
    database_url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for real PostgreSQL verification")

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=database_url,
                escrow_id="production-gate-escrow",
                amount=100,
                currency="MNT",
                witness_id="production-gate-witness",
            ),
            engine=engine,
        )
        runtime = factory.create()

        assert engine.dialect.name == "postgresql"
        assert runtime.is_canonical_ledger_authoritative
        assert runtime._canonical_ledger is not None

        with engine.connect() as connection:
            versions = connection.execute(
                text("SELECT version FROM schema_version ORDER BY version")
            ).scalars().all()
        assert versions == list(range(1, 17))
    finally:
        engine.dispose()
