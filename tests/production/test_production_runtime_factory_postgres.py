from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


@pytest.mark.postgres
def test_production_factory_runs_canonical_migrations_and_boots_authoritative_runtime():
    """Run the actual factory against the disposable PostgreSQL service in core-gates."""
    database_url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is not configured")
    engine = create_engine(database_url, pool_pre_ping=True, future=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=database_url,
                escrow_id="factory-smoke-escrow",
                amount=100,
                currency="MNT",
                witness_id="factory-smoke-witness",
            ),
            engine=engine,
        )
        runtime = factory.create()
        assert runtime.is_canonical_ledger_authoritative is True
        with engine.connect() as connection:
            versions = connection.execute(
                text("SELECT version FROM schema_version ORDER BY version")
            ).scalars().all()
            assert versions == list(range(1, 17))
            connection.execute(text("SELECT 1"))
    finally:
        engine.dispose()
