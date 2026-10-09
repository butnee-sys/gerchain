from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from postgres.migration_runner import apply_migrations, checksum


DATABASE_URL = os.getenv("GERCHAIN_TEST_DATABASE_URL")


@pytest.fixture
def postgres_schema(tmp_path: Path):
    if not DATABASE_URL:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL migration concurrency tests")

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    schema = "migration_test_" + uuid4().hex
    with engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    try:
        yield engine, schema, tmp_path
    finally:
        with engine.begin() as conn:
            conn.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        engine.dispose()


def _connect_to_schema(engine, schema):
    conn = engine.connect()
    conn.exec_driver_sql(f'SET search_path TO "{schema}"')
    conn.commit()
    return conn


def test_duplicate_identical_schema_version_rows_are_reconciled(postgres_schema):
    engine, schema, migrations = postgres_schema
    migration_sql = "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY);"
    migration = migrations / "001_probe.sql"
    migration.write_text(migration_sql, encoding="utf-8")
    digest = checksum(migration_sql)

    with _connect_to_schema(engine, schema) as conn:
        conn.exec_driver_sql(
            "CREATE TABLE schema_version (version BIGINT NOT NULL, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ DEFAULT now())"
        )
        conn.exec_driver_sql(
            "INSERT INTO schema_version(version, checksum) VALUES (1, %s), (1, %s)",
            (digest, digest),
        )
        conn.commit()
        apply_migrations(conn, migrations)
        rows = conn.exec_driver_sql(
            "SELECT version, checksum FROM schema_version WHERE version = 1"
        ).fetchall()
        assert rows == [(1, digest)]
        assert conn.exec_driver_sql(
            "SELECT COUNT(*) FROM migration_probe"
        ).scalar_one() == 0
        conn.commit()


def test_conflicting_checksums_for_same_version_fail_closed(postgres_schema):
    engine, schema, migrations = postgres_schema
    migration_sql = "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY);"
    (migrations / "001_probe.sql").write_text(migration_sql, encoding="utf-8")

    with _connect_to_schema(engine, schema) as conn:
        conn.exec_driver_sql(
            "CREATE TABLE schema_version (version BIGINT NOT NULL, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ DEFAULT now())"
        )
        conn.exec_driver_sql(
            "INSERT INTO schema_version(version, checksum) VALUES (1, %s), (1, %s)",
            ("checksum-a", "checksum-b"),
        )
        conn.commit()
        with pytest.raises(RuntimeError, match="Conflicting schema_version checksums"):
            apply_migrations(conn, migrations)
        rows = conn.exec_driver_sql(
            "SELECT version, checksum FROM schema_version ORDER BY checksum"
        ).fetchall()
        assert rows == [(1, "checksum-a"), (1, "checksum-b")]
        conn.commit()


def test_concurrent_migrators_publish_one_version_record(postgres_schema):
    engine, schema, migrations = postgres_schema
    migration_sql = "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY);"
    (migrations / "001_probe.sql").write_text(migration_sql, encoding="utf-8")

    with engine.begin() as conn:
        conn.exec_driver_sql(f'SET search_path TO "{schema}"')
        conn.exec_driver_sql(
            "CREATE TABLE schema_version (version BIGINT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )

    def run_migrator():
        with _connect_to_schema(engine, schema) as conn:
            apply_migrations(conn, migrations)
            conn.commit()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_migrator) for _ in range(2)]
        for future in futures:
            future.result(timeout=30)

    with _connect_to_schema(engine, schema) as conn:
        rows = conn.exec_driver_sql(
            "SELECT version, checksum FROM schema_version WHERE version = 1"
        ).fetchall()
        assert rows == [(1, checksum(migration_sql))]
        assert conn.exec_driver_sql(
            "SELECT COUNT(*) FROM migration_probe"
        ).scalar_one() == 0
