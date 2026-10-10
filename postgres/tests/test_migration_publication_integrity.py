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


def _version_13_checksum() -> str:
    path = MIGRATION_DIR / "013_ea35_canonical_schema_hardening.sql"
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def test_identical_legacy_duplicate_publication_is_collapsed(isolated_database):
    """Byte-identical legacy duplicates are repaired; versions 1..13 remain unique."""
    migration = MIGRATION_DIR / "001_canonical_production.sql"
    digest = hashlib.sha256(migration.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    with psycopg.connect(isolated_database) as conn:
        # Simulate a legacy history table created before its primary-key constraint.
        conn.execute("CREATE TABLE schema_version (version BIGINT NOT NULL, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        conn.execute("INSERT INTO schema_version(version, checksum) VALUES (1, %s), (1, %s)", (digest, digest))
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
        with pytest.raises(RuntimeError, match="Migration checksum mismatch for version 13"):
            apply_migrations(conn, MIGRATION_DIR)
        rows = conn.execute("SELECT version, checksum FROM schema_version ORDER BY version").fetchall()
        assert rows == [(13, wrong)]
        assert conn.execute("SELECT to_regclass('public.escrows')").fetchone()[0] is None
