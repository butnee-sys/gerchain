from __future__ import annotations

import os

import pytest
from sqlalchemy import inspect, text

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)


@pytest.mark.postgres
def test_production_runtime_boots_on_real_postgresql():
    database_url = os.environ["GERCHAIN_DATABASE_URL"]
    factory = ProductionRuntimeFactory(
        ProductionRuntimeConfig(
            database_url=database_url,
            escrow_id="integration-escrow",
            amount=100,
            currency="USD",
            witness_id="integration-witness",
        )
    )
    runtime = factory.create()

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    required_tables = {
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "gerchain_outbox_events",
        "gerchain_transaction_witnesses",
        "gerchain_idempotency_records",
        "escrows",
    }
    inspector = inspect(factory.engine)
    assert required_tables.issubset(set(inspector.get_table_names()))

    with factory.session_factory() as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1

    factory.engine.dispose()
