"""Real-PostgreSQL regression tests for migration publication and checksum safety."""
from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from postgres.migration_runner import apply_migrations


MIGRATION_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _admin_dsn() -> str:
    value = (
        os.environ.get("GERCHAIN_POSTGRES_DSN")
        or os.environ.get("GERCHAIN_DATABASE_URL")
        or os.environ["GERCHAIN_TEST_DATABASE_URL"]
    )
    return value.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


@pytest.fixture
def isolated_database():
    admin_dsn = _admin_dsn()
    name = f"gerchain_pub_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    dsn = make_conninfo(admin_dsn, dbname=name)
    try:
        yield dsn
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))



def _public_schema_fingerprint(conn) -> tuple[tuple[object, ...], ...]:
    """Capture user-schema objects so checksum rejection proves no DDL escaped."""
    queries = (
        """
        SELECT 'relation', c.relname, c.relkind::text
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
        ORDER BY c.relname, c.relkind
        """,
        """
        SELECT 'column', c.relname, a.attnum::text, a.attname,
               format_type(a.atttypid, a.atttypmod), a.attnotnull::text,
               COALESCE(pg_get_expr(d.adbin, d.adrelid), '')
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid
        LEFT JOIN pg_attrdef d ON d.adrelid = c.oid AND d.adnum = a.attnum
        WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY c.relname, a.attnum
        """,
        """
        SELECT 'constraint', c.relname, con.conname, con.contype::text,
               pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class c ON c.oid = con.conrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
        ORDER BY c.relname, con.conname
        """,
        """
        SELECT 'index', t.relname, i.relname, pg_get_indexdef(i.oid)
        FROM pg_index x
        JOIN pg_class t ON t.oid = x.indrelid
        JOIN pg_class i ON i.oid = x.indexrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public'
        ORDER BY t.relname, i.relname
        """,
        """
        SELECT 'enum', t.typname, e.enumsortorder::text, e.enumlabel
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        JOIN pg_enum e ON e.enumtypid = t.oid
        WHERE n.nspname = 'public'
        ORDER BY t.typname, e.enumsortorder
        """,
    )
    rows: list[tuple[object, ...]] = []
    for query in queries:
        rows.extend(tuple(row) for row in conn.execute(query).fetchall())
    return tuple(sorted(rows, key=repr))


def _version_13_checksum() -> str:
    path = MIGRATION_DIR / "013_ea35_canonical_schema_hardening.sql"
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def test_identical_legacy_duplicate_publication_is_collapsed(isolated_database):
    """Byte-identical legacy duplicates are repaired; versions 1..13 remain unique."""
    with psycopg.connect(isolated_database) as conn:
        # Apply the real schema first so the test exercises duplicate history
        # repair without falsely marking an unapplied migration as complete.
        apply_migrations(conn, MIGRATION_DIR)
        digest = conn.execute(
            "SELECT checksum FROM schema_version WHERE version = 1"
        ).fetchone()[0]
        conn.execute("ALTER TABLE schema_version DROP CONSTRAINT schema_version_pkey")
        conn.execute("DROP INDEX IF EXISTS uq_schema_version_version")
        conn.execute(
            "INSERT INTO schema_version(version, checksum) VALUES (1, %s)",
            (digest,),
        )
        conn.commit()
        apply_migrations(conn, MIGRATION_DIR)
        rows = conn.execute("SELECT version, checksum FROM schema_version ORDER BY version").fetchall()
        assert [row[0] for row in rows] == list(range(1, 14))
        assert len({row[0] for row in rows}) == 13
        assert len({row[0]: row[1] for row in rows}) == 13


def test_conflicting_duplicate_checksums_fail_closed_without_repair(isolated_database):
    with psycopg.connect(isolated_database) as conn:
        conn.execute("CREATE TABLE schema_version (version BIGINT NOT NULL, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        conn.execute("INSERT INTO schema_version(version, checksum) VALUES (1, 'a'), (1, 'b')")
        conn.commit()
        with pytest.raises(RuntimeError, match="Conflicting schema_version checksums"):
            apply_migrations(conn, MIGRATION_DIR)
        rows = conn.execute("SELECT version, checksum FROM schema_version ORDER BY checksum").fetchall()
        assert rows == [(1, "a"), (1, "b")]


def test_applied_checksum_mismatch_rolls_back_and_preserves_history(isolated_database):
    wrong = "0" * 64
    with psycopg.connect(isolated_database) as conn:
        conn.execute("CREATE TABLE schema_version (version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        conn.execute("INSERT INTO schema_version(version, checksum) VALUES (13, %s)", (wrong,))
        conn.commit()
        schema_before = _public_schema_fingerprint(conn)
        version_rows_before = conn.execute(
            "SELECT version, checksum FROM schema_version ORDER BY version"
        ).fetchall()
        with pytest.raises(RuntimeError, match="Migration checksum mismatch for version 13"):
            apply_migrations(conn, MIGRATION_DIR)
        rows = conn.execute("SELECT version, checksum FROM schema_version ORDER BY version").fetchall()
        schema_after = _public_schema_fingerprint(conn)
        assert rows == version_rows_before == [(13, wrong)]
        assert schema_after == schema_before, (
            "checksum rejection changed public schema objects: "
            f"before={schema_before!r}, after={schema_after!r}"
        )
        assert conn.execute("SELECT to_regclass('public.escrows')").fetchone()[0] is None
