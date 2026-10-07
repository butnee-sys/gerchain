import os

import pytest
from sqlalchemy import create_engine, inspect, text

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


def test_production_factory_boots_against_postgresql():
    database_url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL re-performance")

    engine = create_engine(database_url, pool_pre_ping=True)
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="ci-escrow",
            amount=100,
            currency="MNT",
            witness_id="ci-witness",
        ),
        engine=engine,
    )
    runtime = factory.create()

    assert engine.dialect.name == "postgresql"
    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"
    runtime.create_account("ci-boot-account", 17)
    assert runtime.get_balance("ci-boot-account") == 17

    inspector = inspect(engine)
    required = {
        "schema_version",
        "escrows",
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "gerchain_transaction_witnesses",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
    }
    assert required.issubset(set(inspector.get_table_names()))
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT 1 FROM schema_version WHERE version = 1")
        ).scalar_one() == 1

    engine.dispose()
