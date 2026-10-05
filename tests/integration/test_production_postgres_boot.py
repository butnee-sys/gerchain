from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine, inspect, text

from services.gerchain_runtime_factory import ProductionRuntimeConfig, ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def test_production_postgres_migration_and_canonical_boot() -> None:
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is not configured")

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=database_url,
                escrow_id="integration-escrow",
                amount=100,
                currency="MNT",
                witness_id="integration-witness",
            ),
            engine=engine,
        )
        runtime = factory.create()
        assert runtime.is_canonical_ledger_authoritative

        runtime2 = factory.create()
        assert runtime2.is_canonical_ledger_authoritative

        tables = set(inspect(engine).get_table_names())
        required = {
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "escrows",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
        }
        assert not (required - tables)
        assert "schema_version" in tables
        with engine.connect() as connection:
            versions = [row[0] for row in connection.execute(text("SELECT version FROM schema_version ORDER BY version"))]
        assert versions == [1, 2]

        runtime.create_account("integration-source", initial_balance=100)
        runtime.create_account("integration-destination", initial_balance=0)

        first = runtime.settle(
            transaction_id="integration-settlement-1",
            source="integration-source",
            destination="integration-destination",
            amount=25,
            currency="MNT",
        )
        replay = runtime.settle(
            transaction_id="integration-settlement-1",
            source="integration-source",
            destination="integration-destination",
            amount=25,
            currency="MNT",
        )
        assert first["replayed"] is False
        assert replay["replayed"] is True

        with engine.connect() as connection:
            movement_count = connection.execute(
                text("SELECT COUNT(*) FROM gerchain_ledger_movements WHERE transaction_id = :tx"),
                {"tx": "integration-settlement-1"},
            ).scalar_one()
            source_balance = connection.execute(
                text("SELECT balance FROM gerchain_ledger_accounts WHERE account_id = :id"),
                {"id": "integration-source"},
            ).scalar_one()
            destination_balance = connection.execute(
                text("SELECT balance FROM gerchain_ledger_accounts WHERE account_id = :id"),
                {"id": "integration-destination"},
            ).scalar_one()
        assert movement_count == 1
        assert source_balance == 75
        assert destination_balance == 25
    finally:
        engine.dispose()
