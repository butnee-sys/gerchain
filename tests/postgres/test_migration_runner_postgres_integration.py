"""Real-PostgreSQL acceptance tests for the canonical migration runner.

Set GERCHAIN_TEST_POSTGRES_URL to a disposable PostgreSQL database to execute.
Each test uses a dedicated schema and skips (rather than pretending to pass)
when no PostgreSQL endpoint is configured.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
import shutil
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from postgres.migrations import _canonical_migration_files, apply_migrations
from services.gerchain_runtime_factory import assert_canonical_production_schema
from sqlalchemy import create_engine
from persistence.atomic_ledger import AtomicLedgerBase
from persistence.atomic_value_transaction import WitnessBase
from persistence.durable_idempotency import IdempotencyBase
from persistence.escrow_aggregate import EscrowBase
from persistence.recovery_outbox import OutboxBase

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "postgres" / "migrations"
DSN = os.environ.get("GERCHAIN_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="GERCHAIN_TEST_POSTGRES_URL is not configured")


def _schema():
    name = "gc_mig_" + uuid4().hex[:20]
    with psycopg.connect(DSN) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
    return name


def _connect(schema):
    # Server startup option sets search_path without opening a transaction;
    # apply_migrations intentionally requires a clean connection.
    return psycopg.connect(DSN, options=f"-c search_path={schema}")


def _drop_schema(name):
    with psycopg.connect(DSN) as conn:
        conn.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(name)))


def _assert_migration_014_constraints(conn):
    rows = conn.execute(
        """
        SELECT conname, pg_get_constraintdef(oid)
        FROM pg_constraint
        WHERE conrelid = 'escrows'::regclass
          AND contype = 'c'
        ORDER BY conname
        """
    ).fetchall()
    by_name = {name: definition for name, definition in rows}
    assert "legacy_escrow_state_check" not in by_name
    assert "escrows_state_canonical_check" in by_name
    definition = by_name["escrows_state_canonical_check"]
    for state in ("CREATED", "FUNDED", "LOCKED", "RELEASED", "REFUNDED", "CANCELLED"):
        assert state in definition


def test_postgres_upgrade_from_013_preserves_frozen_history_and_applies_014(tmp_path: Path):
    schema = _schema()
    try:
        selected = _canonical_migration_files(MIGRATIONS)
        legacy_dir = tmp_path / "migrations_001_to_013"
        legacy_dir.mkdir()
        for migration in selected:
            version = int(migration.name.split("_", 1)[0])
            if version <= 13:
                shutil.copyfile(migration, legacy_dir / migration.name)

        with _connect(schema) as conn:
            first = apply_migrations(conn, legacy_dir)
            assert first == tuple(range(1, 14))
        with _connect(schema) as conn:
            before = conn.execute(
                "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
            ).fetchall()
            assert [row[0] for row in before] == list(range(1, 14))

        with _connect(schema) as conn:
            applied = apply_migrations(conn, MIGRATIONS)
            assert applied == (14,)
        with _connect(schema) as conn:
            after = conn.execute(
                "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
            ).fetchall()
            assert after[:13] == before
            assert after[13][0] == 14
            _assert_migration_014_constraints(conn)

        with _connect(schema) as conn:
            assert apply_migrations(conn, MIGRATIONS) == ()
        with _connect(schema) as conn:
            final = conn.execute(
                "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
            ).fetchall()
            assert final == after
            _assert_migration_014_constraints(conn)
    finally:
        _drop_schema(schema)


def test_postgres_clean_apply_rerun_and_history_stability():
    schema = _schema()
    try:
        with _connect(schema) as conn:
            first = apply_migrations(conn, MIGRATIONS)
            assert first == tuple(range(1, 15))
        with _connect(schema) as conn:
            before = conn.execute(
                "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
            ).fetchall()
            assert [row[0] for row in before] == list(range(1, 15))
            _assert_migration_014_constraints(conn)

        engine = create_engine(DSN, connect_args={"options": f"-c search_path={schema}"})
        try:
            for base in (AtomicLedgerBase, EscrowBase, WitnessBase, IdempotencyBase, OutboxBase):
                base.metadata.create_all(engine)
            with engine.connect() as connection:
                assert_canonical_production_schema(connection)
        finally:
            engine.dispose()
        with _connect(schema) as conn:
            second = apply_migrations(conn, MIGRATIONS)
            assert second == ()
        with _connect(schema) as conn:
            after = conn.execute(
                "SELECT version, checksum, applied_at FROM schema_version ORDER BY version"
            ).fetchall()
            assert after == before
            _assert_migration_014_constraints(conn)
    finally:
        _drop_schema(schema)


def test_postgres_two_concurrent_runners_publish_each_version_once():
    schema = _schema()
    try:
        def run_once():
            with _connect(schema) as conn:
                return apply_migrations(conn, MIGRATIONS)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: run_once(), range(2)))
        with _connect(schema) as conn:
            rows = conn.execute(
                "SELECT version, COUNT(*) FROM schema_version GROUP BY version ORDER BY version"
            ).fetchall()
        assert [row[0] for row in rows] == list(range(1, 15))
        assert all(row[1] == 1 for row in rows)
        assert sorted(len(result) for result in results) == [0, 14]
        with _connect(schema) as conn:
            _assert_migration_014_constraints(conn)
    finally:
        _drop_schema(schema)


def test_postgres_checksum_mismatch_rolls_back_prior_ddl_and_history(tmp_path: Path):
    # A generic two-file chain lets the test force a checksum mismatch at v2
    # after v1 DDL has executed, proving the enclosing transaction rolls back.
    (tmp_path / "001_first.sql").write_text(
        "CREATE TABLE rollback_probe (id INTEGER PRIMARY KEY);", encoding="utf-8"
    )
    (tmp_path / "002_second.sql").write_text(
        "CREATE TABLE second_probe (id INTEGER PRIMARY KEY);", encoding="utf-8"
    )
    schema = _schema()
    try:
        with _connect(schema) as conn:
            conn.execute(
                """
                CREATE TABLE schema_version (
                    version INTEGER PRIMARY KEY,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            conn.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (2, %s)",
                ("0" * 64,),
            )
        with pytest.raises(RuntimeError, match="Migration checksum mismatch for version 2"):
            with _connect(schema) as conn:
                apply_migrations(conn, tmp_path)
        with _connect(schema) as conn:
            tables = set(conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
                (schema,),
            ).fetchall())
            versions = conn.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
        assert ("rollback_probe",) not in tables
        assert ("second_probe",) not in tables
        assert versions == [(2, "0" * 64)]
    finally:
        _drop_schema(schema)
