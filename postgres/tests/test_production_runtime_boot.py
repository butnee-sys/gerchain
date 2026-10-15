from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from services.gerchain_runtime_factory import ProductionRuntimeFactory
from postgres.migrations import apply_migrations


def test_production_runtime_bootstraps_canonical_persistence():
    database_url = os.environ["GERCHAIN_POSTGRES_DSN"]
    engine = create_engine(database_url, future=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    runtime = ProductionRuntimeFactory.create(
        escrow_id="smoke-escrow",
        amount=100,
        currency="MNT",
        witness_id="smoke-witness",
        engine=engine,
        session_factory=session_factory,
    )

    assert runtime.is_canonical_ledger_authoritative
    assert runtime.runtime_mode == "production-postgresql"

    # Second invocation proves the production migration path is repeat-safe.
    second_runtime = ProductionRuntimeFactory.create(
        escrow_id="smoke-escrow",
        amount=100,
        currency="MNT",
        witness_id="smoke-witness",
        engine=engine,
        session_factory=session_factory,
    )
    assert second_runtime.is_canonical_ledger_authoritative

    with engine.connect() as connection:
        versions = connection.execute(
            text("SELECT version FROM schema_version ORDER BY version")
        ).scalars().all()
        assert versions == list(range(1, 7)), versions
        rows = connection.execute(text(
            "SELECT c.relname, pg_get_constraintdef(k.oid) "
            "FROM pg_constraint k JOIN pg_class c ON c.oid = k.conrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relname IN "
            "('escrows', 'gerchain_ledger_movements', "
            "'gerchain_transaction_witnesses', 'gerchain_idempotency_records') "
            "ORDER BY c.relname, k.conname"
        )).all()
        definitions = [(row[0], row[1]) for row in rows]
        print("CANONICAL_POSTGRES_CONSTRAINTS", definitions)
        assert any(table == "escrows" and "state" in definition.lower()
                   and "CANCELLED" in definition for table, definition in definitions)
        assert any(table == "gerchain_ledger_movements"
                   and "amount" in definition.lower() and "> 0" in definition
                   for table, definition in definitions)
        assert any(table == "gerchain_ledger_movements"
                   and "transaction_id" in definition.lower()
                   and "UNIQUE" in definition.upper()
                   for table, definition in definitions)

    tables = set(inspect(engine).get_table_names())
    assert {
        "gerchain_ledger_accounts",
        "gerchain_ledger_movements",
        "escrows",
        "gerchain_outbox_events",
        "gerchain_idempotency_records",
        "gerchain_transaction_witnesses",
    } <= tables

    engine.dispose()

def test_failed_migration_rolls_back_schema_and_version_record(tmp_path: Path):
    database_url = os.environ["GERCHAIN_POSTGRES_DSN"]
    admin_engine = create_engine(database_url, future=True)
    schema = "migration_rollback_" + uuid4().hex[:12]
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    isolated_engine = create_engine(
        database_url,
        future=True,
        connect_args={"options": f"-csearch_path={schema}"},
    )
    try:
        (tmp_path / "001_probe.sql").write_text(
            "CREATE TABLE gerchain_idempotency_records ("
            "key TEXT PRIMARY KEY, fingerprint VARCHAR(64) NOT NULL, "
            "state VARCHAR(32) NOT NULL, operation VARCHAR(64) NOT NULL);",
            encoding="utf-8",
        )
        (tmp_path / "002_intentional_failure.sql").write_text(
            "THIS IS INTENTIONALLY INVALID SQL;",
            encoding="utf-8",
        )

        with isolated_engine.connect() as connection:
            with pytest.raises(Exception):
                apply_migrations(connection, tmp_path)
            connection.rollback()

        with isolated_engine.connect() as connection:
            tables = set(inspect(connection).get_table_names(schema=schema))
            assert "schema_version" not in tables
            assert "gerchain_idempotency_records" not in tables
    finally:
        isolated_engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()
