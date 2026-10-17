from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
    assert_canonical_production_schema,
)


@pytest.mark.integration
def test_production_postgresql_bootstrap_and_authority():
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is not configured")

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        factory = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=database_url,
                escrow_id="pg-gate-escrow",
                amount=100,
                currency="MNT",
                witness_id="pg-gate-witness",
            ),
            engine=engine,
            session_factory=sessionmaker(bind=engine, expire_on_commit=False),
        )
        runtime = factory.create()

        assert runtime.is_canonical_ledger_authoritative
        assert runtime.runtime_mode == "production-postgresql"

        with engine.connect() as connection:
            assert_canonical_production_schema(connection)
            tables = set(
                connection.execute(
                    text(
                        "SELECT table_name FROM information_schema.tables "
                        "WHERE table_schema = current_schema()"
                    )
                ).scalars()
            )
            assert {
                "escrows",
                "gerchain_ledger_accounts",
                "gerchain_ledger_movements",
                "gerchain_transaction_witnesses",
                "gerchain_outbox_events",
                "gerchain_idempotency_records",
            } <= tables
    finally:
        engine.dispose()
