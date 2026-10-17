from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect, text


@pytest.mark.postgres
def test_production_entrypoint_boots_canonical_postgres_schema(monkeypatch):
    """Run the real entrypoint factory against a dedicated disposable PostgreSQL DB.

    GERCHAIN_TEST_PRODUCTION_DATABASE_URL must point to an isolated test database.
    This test intentionally exercises a separate gate from migration concurrency:
    migration serialization does not prove production runtime boot or schema readiness.
    """
    database_url = os.environ.get("GERCHAIN_TEST_PRODUCTION_DATABASE_URL")
    if not database_url:
        pytest.skip("GERCHAIN_TEST_PRODUCTION_DATABASE_URL is not configured")

    monkeypatch.setenv("GERCHAIN_DATABASE_URL", database_url)
    monkeypatch.setenv("GERCHAIN_ESCROW_ID", "production-boot-test-escrow")
    monkeypatch.setenv("GERCHAIN_ESCROW_AMOUNT", "100")
    monkeypatch.setenv("GERCHAIN_CURRENCY", "MNT")
    monkeypatch.setenv("GERCHAIN_WITNESS_ID", "production-boot-test-witness")

    from production_entrypoint import build_production_runtime
    from services.gerchain_runtime_factory import assert_canonical_production_schema

    runtime = None
    engine = None
    try:
        runtime, engine = build_production_runtime()
        assert runtime.runtime_mode == "production-postgresql"
        assert runtime.is_canonical_ledger_authoritative is True

        with engine.connect() as connection:
            assert_canonical_production_schema(connection)
            versions = connection.execute(
                text("SELECT version FROM schema_version ORDER BY version")
            ).scalars().all()
            assert versions == list(range(1, 17))

            inspector = inspect(connection)
            required = {
                "escrows",
                "gerchain_ledger_accounts",
                "gerchain_ledger_movements",
                "gerchain_transaction_witnesses",
                "gerchain_outbox_events",
                "gerchain_idempotency_records",
            }
            assert required.issubset(set(inspector.get_table_names()))
    finally:
        if engine is not None:
            engine.dispose()
