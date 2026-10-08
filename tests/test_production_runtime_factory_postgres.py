from __future__ import annotations

import os

import pytest

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_production_factory_builds_real_postgresql_runtime():
    database_url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    from sqlalchemy import create_engine
    engine = create_engine(database_url, pool_pre_ping=True)

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="FACTORY-PG-ESC",
            amount=100,
            currency="MNT",
            witness_id="FACTORY-PG-W",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.runtime_mode == "production-postgresql"
    assert runtime.is_canonical_ledger_authoritative is True
    runtime.require_canonical_ledger_authority()
    assert runtime._canonical_ledger is not None
    assert runtime._session_factory is not None
    engine.dispose()

# EA-35 runner synchronization marker: canonical factory API verified.
