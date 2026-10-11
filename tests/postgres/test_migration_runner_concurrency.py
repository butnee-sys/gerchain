from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest

from postgres.migrations import apply_migrations, checksum


DATABASE_URL = os.getenv("GERCHAIN_TEST_DATABASE_URL")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")


@pytest.fixture
def postgres_schema(tmp_path: Path):
    if not DATABASE_URL:
        pytest.skip("GERCHAIN_TEST_DATABASE_URL is required for PostgreSQL migration concurrency tests")

    schema = "migration_test_" + uuid4().hex
    with psycopg.connect(DATABASE_URL, autocommit=True) as admin:
        admin.execute(f'CREATE SCHEMA "{schema}"')
    try:
        yield schema, tmp_path
    finally:
        with psycopg.connect(DATABASE_URL, autocommit=True) as admin:
            admin.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')


def _connect_to_schema(schema: str):
    """Open a fresh psycopg connection using the migration runner's DB-API contract."""
    return psycopg.connect(DATABASE_URL, options=f"-c search_path={schema}")


def test_duplicate_identical_schema_version_rows_are_reconciled(postgres_schema):
    schema, migrations = postgres_schema
    migration_sql = "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY);"
    migration = migrations / "001_probe.sql"
    migration.write_text(migration_sql, encoding="utf-8")
    digest = checksum(migration_sql)

    with _connect_to_schema(schema) as conn:
        conn.execute(
            "CREATE TABLE schema_version (version BIGINT NOT NULL, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ DEFAULT now())"
        )
        conn.execute("CREATE TABLE migration_probe (id INTEGER PRIMARY KEY)")
        conn.execute(
            "INSERT INTO schema_version(version, checksum) VALUES (1, %s), (1, %s)",
            (digest, digest),
        )
        conn.commit()
        apply_migrations(conn, migrations)
        rows = conn.execute(
            "SELECT version, checksum FROM schema_version WHERE version = 1"
        ).fetchall()
        assert rows == [(1, digest)]
        assert conn.execute("SELECT COUNT(*) FROM migration_probe").fetchone()[0] == 0
        conn.commit()



def test_concurrent_bootstrap_creates_registry_once(postgres_schema):
    """Two first-time migrators must serialize before schema_version exists."""
    schema, migrations = postgres_schema
    migration_sql = "CREATE TABLE migration_bootstrap_probe (id INTEGER PRIMARY KEY);"
    (migrations / "001_bootstrap.sql").write_text(migration_sql, encoding="utf-8")

    def run_migrator():
        with _connect_to_schema(schema) as conn:
            apply_migrations(conn, migrations)
            conn.commit()

    # The fixture creates an isolated schema but intentionally does not create
    # schema_version. Both connections race through the first-use bootstrap.
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_migrator) for _ in range(2)]
        for future in futures:
            future.result(timeout=30)

    with _connect_to_schema(schema) as conn:
        rows = conn.execute(
            "SELECT version, checksum FROM schema_version WHERE version = 1"
        ).fetchall()
        assert rows == [(1, checksum(migration_sql))]
        assert conn.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = 'migration_bootstrap_probe'",
            (schema,),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM schema_version WHERE version = 1"
        ).fetchone()[0] == 1


def test_conflicting_checksums_for_same_version_fail_closed(postgres_schema):
    schema, migrations = postgres_schema
    migration_sql = "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY);"
    (migrations / "001_probe.sql").write_text(migration_sql, encoding="utf-8")

    with _connect_to_schema(schema) as conn:
        conn.execute(
            "CREATE TABLE schema_version (version BIGINT NOT NULL, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ DEFAULT now())"
        )
        conn.execute(
            "INSERT INTO schema_version(version, checksum) VALUES (1, %s), (1, %s)",
            ("checksum-a", "checksum-b"),
        )
        conn.commit()
        with pytest.raises(RuntimeError, match="Conflicting schema_version checksums"):
            apply_migrations(conn, migrations)
        rows = conn.execute(
            "SELECT version, checksum FROM schema_version ORDER BY checksum"
        ).fetchall()
        assert rows == [(1, "checksum-a"), (1, "checksum-b")]
        conn.commit()


def test_concurrent_migrators_publish_one_version_record(postgres_schema):
    schema, migrations = postgres_schema
    migration_sql = "CREATE TABLE migration_probe (id INTEGER PRIMARY KEY);"
    (migrations / "001_probe.sql").write_text(migration_sql, encoding="utf-8")

    with _connect_to_schema(schema) as conn:
        conn.execute(
            "CREATE TABLE schema_version (version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        conn.commit()

    def run_migrator():
        with _connect_to_schema(schema) as conn:
            apply_migrations(conn, migrations)
            conn.commit()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_migrator) for _ in range(2)]
        for future in futures:
            future.result(timeout=30)

    with _connect_to_schema(schema) as conn:
        rows = conn.execute(
            "SELECT version, checksum FROM schema_version WHERE version = 1"
        ).fetchall()
        assert rows == [(1, checksum(migration_sql))]
        assert conn.execute("SELECT COUNT(*) FROM migration_probe").fetchone()[0] == 0
