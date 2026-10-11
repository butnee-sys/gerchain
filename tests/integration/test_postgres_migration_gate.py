"""Real PostgreSQL migration gate.

Requires GERCHAIN_TEST_DATABASE_URL pointing at a disposable PostgreSQL database.
This test intentionally does not fall back to SQLite: migration evidence must be
from PostgreSQL itself.
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import create_engine, inspect, text

from postgres.migrations import apply_migrations
from services.gerchain_runtime_factory import (
    ProductionRuntimeConfig,
    ProductionRuntimeFactory,
)

DATABASE_URL = os.getenv("GERCHAIN_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_TEST_DATABASE_URL must point to disposable PostgreSQL",
)


def _driver_url(url: str) -> str:
    from sqlalchemy.engine import make_url

    return make_url(url).set(drivername="postgresql").render_as_string(
        hide_password=False
    )


def test_canonical_migrations_apply_idempotently_on_real_postgres():
    assert DATABASE_URL
    migration_dir = Path(__file__).resolve().parents[2] / "postgres" / "migrations"

    with psycopg.connect(_driver_url(DATABASE_URL)) as conn:
        first = apply_migrations(conn, migration_dir)
    assert first == tuple(range(1, 14))

    with psycopg.connect(_driver_url(DATABASE_URL)) as conn:
        second = apply_migrations(conn, migration_dir)
    assert second == ()

    engine = create_engine(DATABASE_URL)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {
            "schema_version",
            "escrows",
            "gerchain_ledger_accounts",
            "gerchain_ledger_movements",
            "gerchain_transaction_witnesses",
            "gerchain_outbox_events",
            "gerchain_idempotency_records",
        } <= tables

        with engine.connect() as conn:
            versions = conn.execute(
                text("SELECT version FROM schema_version ORDER BY version")
            ).scalars().all()
            assert versions == list(range(1, 14))

            constraints = conn.execute(
                text(
                    """
                    SELECT conname
                    FROM pg_constraint
                    WHERE conname IN (
                        'gerchain_ledger_balance_nonnegative',
                        'gerchain_movement_distinct_accounts',
                        'gerchain_witness_event_type_check',
                        'gerchain_outbox_state_check',
                        'gerchain_idempotency_fingerprint_check',
                        'escrows_amount_positive_check'
                    )
                    """
                )
            ).scalars().all()
            assert len(set(constraints)) == 6
    finally:
        engine.dispose()


def test_production_factory_uses_canonical_ledger_on_real_postgres():
    assert DATABASE_URL
    engine = create_engine(DATABASE_URL)
    try:
        runtime = ProductionRuntimeFactory(
            ProductionRuntimeConfig(
                database_url=DATABASE_URL,
                escrow_id="migration-gate-escrow",
                amount=1,
                currency="MNT",
                witness_id="migration-gate-witness",
            ),
            engine=engine,
        ).create()
        assert runtime.is_canonical_ledger_authoritative
        assert runtime._canonical_ledger is not None
        assert runtime._session_factory is not None
    finally:
        engine.dispose()
