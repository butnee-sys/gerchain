from __future__ import annotations

import os

import pytest

from services.production_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


@pytest.mark.integration
def test_production_factory_builds_real_postgresql_runtime():
    database_url = os.getenv("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="FACTORY-PG-ESC",
            amount=100,
            currency="MNT",
            witness_id="FACTORY-PG-W",
        )
    )
    runtime = factory.create()

    assert runtime.runtime_mode == "production-postgresql"
    assert runtime.is_postgresql_authoritative is True
    runtime.require_postgresql_authority()
    assert runtime._postgres_release is not None
    assert runtime._postgres_release._release.session_factory is factory.session_factory
