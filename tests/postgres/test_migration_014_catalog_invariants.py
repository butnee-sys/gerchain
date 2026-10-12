from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg
import pytest


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "postgres" / "migrations" / "014_canonical_escrow_state_constraint.sql"
DSN = (
    os.environ.get("GERCHAIN_MIGRATION_TEST_DSN")
    or os.environ.get("GERCHAIN_POSTGRES_DSN")
    or os.environ.get("GERCHAIN_DATABASE_URL")
)


@pytest.fixture
def isolated_schema():
    if not DSN:
        pytest.skip("requires a real PostgreSQL DSN")
    schema = "migration014_" + uuid.uuid4().hex
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{schema}"')
        try:
            conn.execute(f'SET search_path TO "{schema}"')
            conn.execute(
                """
                CREATE TABLE escrows (
                    id text PRIMARY KEY,
                    state text NOT NULL,
                    CONSTRAINT legacy_escrow_state_check
                    CHECK (state IN ('CREATED', 'LOCKED', 'RELEASED')),
                    CONSTRAINT escrows_state_canonical_check
                    CHECK (state IN ('CREATED', 'FUNDED', 'LOCKED', 'RELEASED', 'REFUNDED', 'CANCELLED'))
                )
                """
            )
            yield conn, schema
        finally:
            conn.execute("SET search_path TO public")
            conn.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def _constraint_snapshot(conn):
    return conn.execute(
        """
        SELECT c.conname,
               c.contype,
               pg_get_constraintdef(c.oid, true) AS definition,
               ARRAY(
                   SELECT a.attname
                   FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
                   JOIN pg_attribute a
                     ON a.attrelid = c.conrelid AND a.attnum = k.attnum
                   ORDER BY k.ord
               ) AS column_order
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = current_schema()
          AND t.relname = 'escrows'
          AND c.contype = 'c'
        ORDER BY c.conname
        """
    ).fetchall()


def test_migration_014_standalone_is_repeatable_and_preserves_canonical_constraint(isolated_schema):
    conn, _schema = isolated_schema
    sql = MIGRATION.read_text(encoding="utf-8")

    conn.execute(sql)
    first = _constraint_snapshot(conn)
    conn.execute(sql)
    second = _constraint_snapshot(conn)

    assert first == second, "rerunning migration 014 changed constraint identity or shape"
    assert [row[0] for row in second] == [
        "escrows_state_canonical_check",
    ]
    name, kind, definition, columns = second[0]
    assert kind == "c"
    assert columns == ["state"]
    normalized = " ".join(definition.lower().split())
    for state in ("created", "funded", "locked", "released", "refunded", "cancelled"):
        assert state in normalized
    assert conn.execute(
        """
        SELECT count(*)
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = current_schema()
          AND t.relname = 'escrows'
          AND c.conname = 'legacy_escrow_state_check'
        """
    ).fetchone()[0] == 0


def test_escrow_orm_metadata_does_not_own_state_constraint():
    from sqlalchemy import CheckConstraint
    from persistence.escrow_aggregate import CanonicalEscrow

    checks = [
        constraint
        for constraint in CanonicalEscrow.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]
    assert checks == [], (
        "escrow lifecycle state constraints are migration-owned DDL; "
        "ORM metadata must not create a competing constraint authority"
    )
