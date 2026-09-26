import os

import pytest
from sqlalchemy import create_engine, inspect

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)
from persistence.deep_value_reconciliation import deep_reconcile_value_truth


@pytest.mark.integration
def test_production_postgres_boot_and_schema_guard():
    database_url = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required")

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=database_url,
                escrow_id="integration-escrow",
                amount=100,
                currency="USD",
                witness_id="integration-witness",
            ),
            engine=engine,
        )
        runtime = factory.create()

        assert runtime.is_canonical_ledger_authoritative is True

        inspector = inspect(engine)
        required_tables = {
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "escrows",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
        }
        assert required_tables.issubset(set(inspector.get_table_names()))

        with factory.session_factory() as session:
            report = deep_reconcile_value_truth(session)
            assert report.matched is True
            assert not report.issues
    finally:
        engine.dispose()
