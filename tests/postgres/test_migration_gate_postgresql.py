"""Real PostgreSQL proof for the canonical 001..016 migration gate.

Set GERCHAIN_TEST_DATABASE_URL to a disposable PostgreSQL database. Tests create
and drop an isolated schema; they never target public schema directly.
"""
from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

import psycopg
import pytest

from postgres.migrations import apply_migrations


DATABASE_URL = os.environ.get("GERCHAIN_TEST_DATABASE_URL")
MIGRATION_DIR = Path(__file__).resolve().parents[2] / "postgres" / "migrations"
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_TEST_DATABASE_URL must point to a disposable PostgreSQL database",
)


def _schema_snapshot(connection, schema: str) -> tuple:
    """Stable schema/history fingerprint for migration idempotency checks."""
    relations = connection.execute(
        """
        SELECT c.relname, c.relkind
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relkind IN ('r', 'p', 'v', 'm', 'S')
        ORDER BY c.relname, c.relkind
        """,
        (schema,),
    ).fetchall()
    columns = connection.execute(
        """
        SELECT table_name, column_name, ordinal_position, data_type,
               is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s
        ORDER BY table_name, ordinal_position
        """,
        (schema,),
    ).fetchall()
    constraints = connection.execute(
        """
        SELECT table_name, constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE constraint_schema = %s
        ORDER BY table_name, constraint_name, constraint_type
        """,
        (schema,),
    ).fetchall()
    indexes = connection.execute(
        """
        SELECT tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = %s
        ORDER BY tablename, indexname
        """,
        (schema,),
    ).fetchall()
    triggers = connection.execute(
        """
        SELECT c.relname, t.tgname, pg_get_triggerdef(t.oid, true)
        FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND NOT t.tgisinternal
        ORDER BY c.relname, t.tgname
        """,
        (schema,),
    ).fetchall()
    functions = connection.execute(
        """
        SELECT p.proname, pg_get_functiondef(p.oid)
        FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = %s AND p.prokind IN ('f', 'p')
        ORDER BY p.proname, pg_get_functiondef(p.oid)
        """,
        (schema,),
    ).fetchall()
    history = connection.execute(
        f'SELECT version, checksum FROM "{schema}".schema_version ORDER BY version'
    ).fetchall()
    return (tuple(relations), tuple(columns), tuple(constraints), tuple(indexes), tuple(triggers), tuple(functions), tuple(history))


def test_postgresql_clean_migration_rerun_and_checksum_drift_are_safe(tmp_path: Path):
    schema = "mig_gate_" + uuid.uuid4().hex
    with psycopg.connect(DATABASE_URL, autocommit=True) as admin:
        admin.execute(f'CREATE SCHEMA "{schema}"')
    try:
        # PostgreSQL search_path isolates every unqualified migration object.
        with psycopg.connect(DATABASE_URL, options=f"-c search_path={schema},public") as connection:
            first = apply_migrations(connection, MIGRATION_DIR)
            assert first == tuple(range(1, 17))

            history = connection.execute(
                f'SELECT version, checksum FROM "{schema}".schema_version ORDER BY version'
            ).fetchall()
            assert [version for version, _ in history] == list(range(1, 17))
            assert len({version for version, _ in history}) == 16
            assert all(len(digest) == 64 for _, digest in history)
            assert all(
                all(character in "0123456789abcdef" for character in digest)
                for _, digest in history
            )

            before_rerun = _schema_snapshot(connection, schema)
            second = apply_migrations(connection, MIGRATION_DIR)
            after_rerun = _schema_snapshot(connection, schema)
            assert second == ()
            assert after_rerun == before_rerun

            changed_dir = tmp_path / "migrations"
            shutil.copytree(MIGRATION_DIR, changed_dir)
            first_migration = changed_dir / "001_canonical_production.sql"
            first_migration.write_text(
                first_migration.read_text(encoding="utf-8") + "\n-- intentional checksum drift test\n",
                encoding="utf-8",
            )
            before_drift_attempt = _schema_snapshot(connection, schema)
            with pytest.raises(RuntimeError, match="Migration checksum mismatch for version 1"):
                apply_migrations(connection, changed_dir)
            after_drift_attempt = _schema_snapshot(connection, schema)
            assert after_drift_attempt == before_drift_attempt
    finally:
        with psycopg.connect(DATABASE_URL, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
