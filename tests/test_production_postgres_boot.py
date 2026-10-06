import os

import pytest
from sqlalchemy import create_engine, inspect, text

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


@pytest.mark.integration
def test_production_runtime_boots_on_postgresql():
    url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not url:
        pytest.skip("GERCHAIN_DATABASE_URL is not configured")

    engine = create_engine(url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=url,
            escrow_id="smoke-escrow",
            amount=100,
            currency="MNT",
            witness_id="smoke-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())
        required = {
            "schema_version",
            "escrows",
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
        }
        assert required <= tables
        version = connection.execute(
            text("SELECT MAX(version) FROM schema_version")
        ).scalar_one()
        assert version == 5

    engine.dispose()
