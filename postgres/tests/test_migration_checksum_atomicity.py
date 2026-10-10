import os
from pathlib import Path
import uuid

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from postgres.migrations import apply_migrations


def _dsn() -> str:
    value = os.environ.get("GERCHAIN_POSTGRES_DSN") or os.environ.get("GERCHAIN_DATABASE_URL") or os.environ["GERCHAIN_TEST_DATABASE_URL"]
    return value.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")


def test_checksum_mismatch_rolls_back_without_partial_schema_or_history(tmp_path: Path):
    admin_dsn = _dsn()
    database_name = f"gerchain_checksum_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        admin.execute("CREATE DATABASE " + '"'"'"'"' + database_name + '"'"'"'"'"')

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
            admin.execute("DROP DATABASE IF EXISTS " + '"'"'"'"' + database_name + '"'"'"'"' + " WITH (FORCE)")
