from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest


DATABASE_URL = os.getenv("GERCHAIN_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="GERCHAIN_TEST_DATABASE_URL must point to a disposable PostgreSQL database",
)


def _constraint_snapshot(connection, schema: str) -> tuple[tuple[str, str, bool], ...]:
    rows = connection.execute(
        """
        SELECT c.conname, pg_get_constraintdef(c.oid, true), c.convalidated
        FROM pg_constraint AS c
        JOIN pg_class AS t ON t.oid = c.conrelid
        JOIN pg_namespace AS n ON n.oid = t.relnamespace
        WHERE n.nspname = %s AND t.relname = 'escrows'
        ORDER BY c.conname
        """,
        (schema,),
    ).fetchall()
    return tuple((name, definition, validated) for name, definition, validated in rows)


def _apply_migration(connection, schema: str, sql: str) -> None:
    connection.execute(f'SET search_path TO "{schema}"')
    connection.execute(sql)


def test_014_escrow_state_constraint_is_idempotent_and_preserves_definition():
    """Compare one versus two applications in isolated schemas, including legacy DDL."""
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "postgres"
        / "migrations"
        / "014_canonical_escrow_state_constraint.sql"
    )
    migration_sql = migration_path.read_text(encoding="utf-8")
    suffix = uuid.uuid4().hex[:12]
    once_schema = f"ea35_once_{suffix}"
    twice_schema = f"ea35_twice_{suffix}"

    with psycopg.connect(DATABASE_URL) as connection:
        try:
            for schema in (once_schema, twice_schema):
                connection.execute(f'CREATE SCHEMA "{schema}"')
                connection.execute(f'SET search_path TO "{schema}"')
                connection.execute(
                    """
                    CREATE TABLE escrows (
                        id TEXT PRIMARY KEY,
                        state TEXT NOT NULL,
                        CONSTRAINT legacy_escrow_state_check
                            CHECK (state IN ('CREATED', 'LOCKED', 'RELEASED'))
                    )
                    """
                )
                # Capture the exact pre-migration constraint definition from the
                # schema fixture before running the migration.
                old = connection.execute(
                    """
                    SELECT c.conname, pg_get_constraintdef(c.oid, true), c.convalidated
                    FROM pg_constraint c
                    JOIN pg_class t ON t.oid = c.conrelid
                    JOIN pg_namespace n ON n.oid = t.relnamespace
                    WHERE n.nspname = %s AND t.relname = 'escrows'
                    ORDER BY c.conname
                    """,
                    (schema,),
                ).fetchall()
                assert old == [
                    (
                        "legacy_escrow_state_check",
                        "CHECK ((state = ANY (ARRAY['CREATED'::text, 'LOCKED'::text, 'RELEASED'::text])))",
                        True,
                    )
                ]

            _apply_migration(connection, once_schema, migration_sql)
            once_snapshot = _constraint_snapshot(connection, once_schema)

            _apply_migration(connection, twice_schema, migration_sql)
            _apply_migration(connection, twice_schema, migration_sql)
            twice_snapshot = _constraint_snapshot(connection, twice_schema)

            assert once_snapshot == twice_snapshot
            assert once_snapshot == (
                (
                    "escrows_state_canonical_check",
                    "CHECK ((state = ANY (ARRAY['CREATED'::text, 'FUNDED'::text, 'LOCKED'::text, 'RELEASED'::text, 'REFUNDED'::text, 'CANCELLED'::text])))",
                    True,
                ),
            )
        finally:
            connection.execute("SET search_path TO public")
            connection.execute(f'DROP SCHEMA IF EXISTS "{once_schema}" CASCADE')
            connection.execute(f'DROP SCHEMA IF EXISTS "{twice_schema}" CASCADE')
