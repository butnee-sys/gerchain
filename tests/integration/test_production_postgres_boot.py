from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from postgres.migrations import apply_migrations
from services.gerchain_runtime_factory import ProductionRuntimeFactory


pytestmark = pytest.mark.integration


def test_production_postgres_migration_and_canonical_boot() -> None:
    database_url = os.environ.get("GERCHAIN_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_DATABASE_URL is not configured")

    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            apply_migrations(conn, Path(__file__).parents[2] / "postgres" / "migrations")

        runtime = ProductionRuntimeFactory.create(
            escrow_id="integration-escrow",
            amount=100,
            currency="MNT",
            witness_id="integration-witness",
            engine=engine,
            session_factory=sessionmaker(bind=engine, expire_on_commit=False),
        )
        assert runtime.is_canonical_ledger_authoritative

        runtime2 = ProductionRuntimeFactory.create(
            escrow_id="integration-escrow",
            amount=100,
            currency="MNT",
            witness_id="integration-witness",
            engine=engine,
            session_factory=lambda: __import__("sqlalchemy.orm", fromlist=["sessionmaker"]).sessionmaker(bind=engine, expire_on_commit=False)(),
        )
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
    finally:
        engine.dispose()
