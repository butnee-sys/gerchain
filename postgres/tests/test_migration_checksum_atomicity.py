import os
from pathlib import Path
import uuid

import psycopg
from psycopg import sql
import pytest
from psycopg.conninfo import make_conninfo

from postgres.migrations import apply_migrations


def _dsn() -> str:
    value = (os.environ.get("GERCHAIN_POSTGRES_DSN") or os.environ.get("GERCHAIN_DATABASE_URL") or os.environ.get("GERCHAIN_TEST_DATABASE_URL") or os.environ["GERCHAIN_MIGRATION_TEST_DATABASE_URL"])
    return value.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")


def test_legacy_registry_collapses_identical_publications_and_enforces_unique_version(tmp_path: Path):
    admin_dsn = _dsn()
    database_name = f"gerchain_legacy_registry_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    dsn = make_conninfo(admin_dsn, dbname=database_name)
    migration = tmp_path / "001_legacy_registry.sql"
    source = "CREATE TABLE legacy_registry_probe (id INTEGER PRIMARY KEY);"
    migration.write_text(source, encoding="utf-8")
    from postgres.migrations import checksum

    digest = checksum(source)
    try:
        with psycopg.connect(dsn) as connection:
            # Simulate a pre-canonical registry: same schema, but no PK/unique
            # constraint and duplicate publications from a legacy runner.
            connection.execute(
                "CREATE TABLE schema_version (version INTEGER NOT NULL, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ DEFAULT now())"
            )
            connection.execute(
                "INSERT INTO schema_version(version, checksum) VALUES (1, %s), (1, %s)",
                (digest, digest),
            )
            connection.commit()

        with psycopg.connect(dsn) as connection:
            applied = apply_migrations(connection, tmp_path)
            assert applied == ()

        with psycopg.connect(dsn) as connection:
            rows = connection.execute(
                "SELECT version, checksum FROM schema_version ORDER BY version"
            ).fetchall()
            unique_version_index = connection.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_index AS idx
                    JOIN pg_attribute AS attr
                      ON attr.attrelid = idx.indrelid
                     AND attr.attnum = idx.indkey[0]
                    WHERE idx.indrelid = 'schema_version'::regclass
                      AND idx.indisunique
                      AND idx.indpred IS NULL
                      AND idx.indnkeyatts = 1
                      AND attr.attname = 'version'
                )
                """
            ).fetchone()[0]
        assert rows == [(1, digest)], f"duplicate version publication remains: {rows!r}"
        assert unique_version_index, "schema_version.version is not protected by a unique index"
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))


def test_checksum_mismatch_rolls_back_without_partial_schema_or_history(tmp_path: Path):
    admin_dsn = _dsn()
    database_name = f"gerchain_checksum_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))

    dsn = make_conninfo(admin_dsn, dbname=database_name)
    first = tmp_path / "001_first.sql"
    second = tmp_path / "002_second.sql"
    first.write_text("CREATE TABLE checksum_probe (id INTEGER PRIMARY KEY);", encoding="utf-8")
    try:
        with psycopg.connect(dsn) as connection:
            apply_migrations(connection, tmp_path)
        # Reapplying the same migration source/checksum is idempotent: it must
        # not publish a duplicate schema_version row.
        with psycopg.connect(dsn) as connection:
            apply_migrations(connection, tmp_path)
        with psycopg.connect(dsn) as connection:
            before = connection.execute("SELECT version, checksum FROM schema_version ORDER BY version").fetchall()
            assert [row[0] for row in before] == [1]
            assert len(before) == 1, f"duplicate migration publication: {before!r}"

        # Tamper with an already-published migration and introduce a later one.
        first.write_text("CREATE TABLE checksum_probe (id INTEGER PRIMARY KEY, note TEXT);", encoding="utf-8")
        second.write_text("CREATE TABLE should_rollback (id INTEGER PRIMARY KEY);", encoding="utf-8")
        with psycopg.connect(dsn) as connection:
            with pytest.raises(RuntimeError, match="Migration checksum mismatch for version 1"):
                apply_migrations(connection, tmp_path)

        with psycopg.connect(dsn) as connection:
            after = connection.execute("SELECT version, checksum FROM schema_version ORDER BY version").fetchall()
            tables = {row[0] for row in connection.execute("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()").fetchall()}
        assert after == before, f"schema_version changed after checksum failure: before={before!r}, after={after!r}"
        assert "checksum_probe" in tables
        assert "should_rollback" not in tables
    finally:
        with psycopg.connect(admin_dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))
